variable "region" {
  type    = string
  default = "me-central-1"
}

variable "project" {
  type    = string
  default = "cargopulse"
}

variable "environment" {
  type    = string
  default = "dev"
}

variable "vpc_cidr" {
  type    = string
  default = "10.0.0.0/16"
}

variable "az_count" {
  type    = number
  default = 2
}

variable "single_nat_gateway" {
  type        = bool
  default     = true
  description = "true = one shared NAT (cheap, dev). false = one NAT per AZ (high availability, prod)."
}

variable "container_port" {
  type    = number
  default = 8000
}

variable "image_tag" {
  type    = string
  default = "latest"
}

variable "desired_count" {
  type    = number
  default = 2
}

variable "task_cpu" {
  type    = number
  default = 256
}

variable "task_memory" {
  type    = number
  default = 512
}

variable "db_instance_class" {
  type    = string
  default = "db.t3.micro"
}

variable "db_allocated_storage" {
  type    = number
  default = 20
}

variable "db_multi_az" {
  type        = bool
  default     = false
  description = "Standby replica in a 2nd AZ. Turn on for production."
}
