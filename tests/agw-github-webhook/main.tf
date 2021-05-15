terraform {
  required_version = "0.14.8"
  required_providers {
    testing = {
      source  = "apparentlymart/testing"
      version = "0.0.2"
    }
    random = {
      source  = "hashicorp/random"
      version = "3.1.0"
    }
  }
}

locals {
  repo_name = "mut-agw-github-webhook-${random_id.this.id}"
  not_sha_sig_input = jsonencode({
    "headers" = {
      "X-Hub-Signature-256" = sha256("test")
      "X-GitHub-Event" : "push"
    }
    "body" = {}
  })
  invalid_sig_input = jsonencode({
    "headers" = {
      "X-Hub-Signature-256" = "sha256=${sha256("test")}"
      "X-GitHub-Event" : "push"
    }
    "body" = {}
  })
}

provider "random" {}

resource "random_password" "this" {
  length = 20
}

resource "random_id" "this" {
  byte_length = 8
}

resource "github_repository" "test" {
  name        = local.repo_name
  description = "Test repo for mut: terraform-aws-lambda/agw-github-webhook"
  auto_init   = true
  visibility  = "public"
}

resource "github_repository_file" "test" {
  repository          = github_repository.test.name
  branch              = "master"
  file                = "test.txt"
  content             = "used to trigger repo's webhook for testing associated mut: agw-github-webhook"
  commit_message      = "test file"
  overwrite_on_create = true
  depends_on = [
    module.mut_agw_github_webhook
  ]
}

module "mut_agw_github_webhook" {
  source = "../../modules/agw-github-webhook"
  repos = [
    {
      name   = local.repo_name
      events = ["push"]
    }
  ]
  create_github_secret_ssm_param = true
  github_secret_ssm_value        = random_password.this.result
  depends_on = [
    github_repository.test
  ]
}