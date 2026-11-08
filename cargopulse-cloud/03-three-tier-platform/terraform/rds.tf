resource "aws_db_subnet_group" "main" {
  name       = "${local.name}-db"
  subnet_ids = aws_subnet.db[*].id
}

resource "aws_db_instance" "main" {
  identifier     = "${local.name}-pg"
  engine         = "postgres"
  engine_version = "16"
  instance_class = var.db_instance_class

  allocated_storage = var.db_allocated_storage
  storage_encrypted = true

  db_name  = "cargopulse"
  username = "cargopulse_admin"
  # RDS generates the password and keeps it in Secrets Manager.
  # No password ever appears in code, tfvars, or Terraform config.
  manage_master_user_password = true

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.db.id]
  publicly_accessible    = false
  multi_az               = var.db_multi_az

  backup_retention_period    = 7
  auto_minor_version_upgrade = true

  # Demo settings so `terraform destroy` works. For production: keep a final snapshot
  # and enable deletion protection.
  skip_final_snapshot = true
  deletion_protection = false
}
