terraform {
  required_version = ">=0.15.0"
  required_providers {
    random = {
      source  = "hashicorp/random"
      version = "3.1.0"
    }
    github = {
      source  = "integrations/github"
      version = "4.9.3"
    }
  }
}
