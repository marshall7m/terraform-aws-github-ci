terraform {
  required_version = ">=1.0.0"
  experiments      = [module_variable_optional_attrs]
  required_providers {
    github = {
      source  = "integrations/github"
      version = ">=4.9.3"
    }
    random = {
      source  = "hashicorp/random"
      version = ">=3.3.1"
    }
  }
}