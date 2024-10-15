variable "aws_region" {
  description = "The AWS region this application will run in"
  default     = "us-west-2"
}

variable "unique_identifier" {
  description = "A unique identifier for naming resources to avoid name collisions"
  validation {
    condition     = can(regex("^[a-z]{6,10}$", var.unique_identifier))
    error_message = "unique_identifier must be lower case letters only and 6 to 10 characters in length"
  }
}

variable "app_name" {
  description = "Name of the application this configuration is creating"
}

variable "ld_api_key" {
  description = "LaunchDarkly API key"
}

variable "owner" {
  description = "Your email address"
}
