terraform {
  required_version = "0.15.0"
  experiments      = [module_variable_optional_attrs]
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = ">= 2.23"
    }
    github = {
      source  = "integrations/github"
      version = ">= 4.4.0"
    }
    archive = {
      source  = "hashicorp/archive"
      version = ">=2.2.0"
    }
    local = {
      source  = "hashicorp/local"
      version = ">=2.1.0"
    }
    null = {
      source  = "hashicorp/null"
      version = ">=3.1.0"
    }
  }
}