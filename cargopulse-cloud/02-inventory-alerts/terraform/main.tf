data "aws_caller_identity" "me" {}

locals {
  name = "${var.project}-inventory"
}

# ---------- S3 bucket for incoming stock files ----------
resource "aws_s3_bucket" "stock" {
  bucket        = "${local.name}-${data.aws_caller_identity.me.account_id}"
  force_destroy = true # demo project: allow terraform destroy with files inside
}

resource "aws_s3_bucket_public_access_block" "stock" {
  bucket                  = aws_s3_bucket.stock.id
  block_public_acls       = true
  block_public_policy     = true
  ignore_public_acls      = true
  restrict_public_buckets = true
}

resource "aws_s3_bucket_server_side_encryption_configuration" "stock" {
  bucket = aws_s3_bucket.stock.id
  rule {
    apply_server_side_encryption_by_default {
      sse_algorithm = "AES256"
    }
  }
}

# ---------- SNS ----------
resource "aws_sns_topic" "alerts" {
  name = "${local.name}-alerts"
}

resource "aws_sns_topic_subscription" "email" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# ---------- Lambda ----------
data "archive_file" "lambda" {
  type        = "zip"
  source_dir  = "${path.module}/../src"
  output_path = "${path.module}/build/handler.zip"
}

data "aws_iam_policy_document" "assume" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "lambda" {
  name               = "${local.name}-lambda"
  assume_role_policy = data.aws_iam_policy_document.assume.json
}

resource "aws_iam_role_policy_attachment" "logs" {
  role       = aws_iam_role.lambda.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

data "aws_iam_policy_document" "access" {
  statement {
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.stock.arn}/incoming/*"]
  }
  statement {
    actions   = ["sns:Publish"]
    resources = [aws_sns_topic.alerts.arn]
  }
}

resource "aws_iam_role_policy" "access" {
  name   = "s3-read-sns-publish"
  role   = aws_iam_role.lambda.id
  policy = data.aws_iam_policy_document.access.json
}

resource "aws_cloudwatch_log_group" "lambda" {
  name              = "/aws/lambda/${local.name}"
  retention_in_days = 14
}

resource "aws_lambda_function" "checker" {
  function_name    = local.name
  role             = aws_iam_role.lambda.arn
  runtime          = "python3.12"
  handler          = "handler.lambda_handler"
  filename         = data.archive_file.lambda.output_path
  source_code_hash = data.archive_file.lambda.output_base64sha256
  timeout          = 30
  memory_size      = 128

  environment {
    variables = {
      TOPIC_ARN = aws_sns_topic.alerts.arn
    }
  }

  depends_on = [aws_cloudwatch_log_group.lambda]
}

# ---------- S3 -> Lambda trigger ----------
resource "aws_lambda_permission" "s3" {
  statement_id   = "AllowS3Invoke"
  action         = "lambda:InvokeFunction"
  function_name  = aws_lambda_function.checker.function_name
  principal      = "s3.amazonaws.com"
  source_arn     = aws_s3_bucket.stock.arn
  source_account = data.aws_caller_identity.me.account_id
}

resource "aws_s3_bucket_notification" "stock" {
  bucket = aws_s3_bucket.stock.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.checker.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "incoming/"
    filter_suffix       = ".csv"
  }

  depends_on = [aws_lambda_permission.s3]
}
