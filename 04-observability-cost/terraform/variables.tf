variable "region" {
  type    = string
  default = "me-central-1"
}

variable "project" {
  type    = string
  default = "cargopulse"
}

variable "alert_email" {
  type = string
}

variable "monthly_budget_usd" {
  type    = number
  default = 50
}

# The next five values come from `terraform output` in 03-three-tier-platform/terraform
variable "ecs_cluster_name" {
  type = string
}

variable "ecs_service_name" {
  type = string
}

variable "alb_arn_suffix" {
  type = string
}

variable "target_group_arn_suffix" {
  type = string
}

variable "db_instance_id" {
  type = string
}
