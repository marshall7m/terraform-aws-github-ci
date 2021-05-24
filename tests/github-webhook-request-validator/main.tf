locals {
  repo_name = "mut-agw-github-webhook-${random_id.this.id}"
  invalid_sig_input = jsonencode({
    "headers" = {
      "X-Hub-Signature-256" = "sha256=${sha256("test")}"
      "X-GitHub-Event" : "push"
    }
    "body" = {}
  })
}

provider "random" {}

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
  source = "../../modules/github-webhook-request-validator"
  repos = [
    {
      name   = local.repo_name
      events = ["push"]
    }
  ]
  depends_on = [
    github_repository.test
  ]
}

data "aws_lambda_invocation" "not_sha_signed" {
  function_name = module.mut_dynamic_github_source.function_name

  input = jsonencode(
    {
      "headers" = {
        "X-Hub-Signature-256" = sha256("test")
        "X-GitHub-Event" : "push"
      }
      "body" = {}
    }
  )
}

resource "test_assertions" "request_validator" {
  component = "test_requests"

  equal "not_sha_signed" {
    description = "payload"
    got         = { for key, value in jsondecode(data.aws_lambda_invocation.not_sha_signed.result) : key => jsondecode(value) }
    want = {
      "statusCode" = 403,
      "body"       = { "error" = "signature is invalid" }
    }
  }
}
