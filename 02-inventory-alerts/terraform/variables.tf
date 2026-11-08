variable "region" {
  type    = string
  default = "me-central-1"
}

variable "project" {
  type    = string
  default = "cargopulse"
}

variable "alert_email" {
  type        = string
  description = "Email that receives low-stock alerts (you must confirm the subscription)"
}
