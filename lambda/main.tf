locals {
  rgrunner_fname    = "${var.unique_identifier}_lambda_rgrunner"
  rgrunner_loggroup = "/aws/lambda/${local.rgrunner_fname}"
}

provider "aws" {
  region = var.aws_region
}

provider "archive" {}
