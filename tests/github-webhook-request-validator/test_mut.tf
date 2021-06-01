locals {
  mut       = basename(path.cwd)
  repo_name = "mut-${local.mut}-${random_id.this.id}"
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
    module.mut_github_webhook_request_validator
  ]
}

module "mut_github_webhook_request_validator" {
  source = "../../modules/github-webhook-request-validator"

  api_name = "mut-${local.mut}"
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

resource "null_resource" "not_sha_signed" {
  triggers = {
    run = timestamp()
  }
  provisioner "local-exec" {
    command = <<EOF
aws lambda invoke \
  --function-name ${module.mut_github_webhook_request_validator.function_name} \
  --payload "${base64encode(jsonencode({
    "headers" = {
      "X-Hub-Signature-256" = sha256("test")
      "X-GitHub-Event" : "push"
    }
    "body" = {}
}))}" \
  tmp/not_sha_signed.json
EOF
}

depends_on = [
  module.mut_github_webhook_request_validator
]
}

resource "null_resource" "invalid_sha_sig" {
  triggers = {
    run = timestamp()
  }
  provisioner "local-exec" {
    command = <<EOF
aws lambda invoke \
  --function-name ${module.mut_github_webhook_request_validator.function_name} \
  --payload "${base64encode(jsonencode({
    "headers" = {
      "X-Hub-Signature-256" = "sha256=${sha256("test")}"
      "X-GitHub-Event" : "push"
    }
    "body" = {}
}))}" \
  ${path.cwd}/tmp/invalid_sha_sig.json
EOF
}

depends_on = [
  module.mut_github_webhook_request_validator
]
}

data "local_file" "not_sha_signed" {
  filename = "tmp/not_sha_signed.json"
  depends_on = [
    null_resource.not_sha_signed
  ]
}

data "local_file" "invalid_sha_sig" {
  filename = "tmp/invalid_sha_sig.json"
  depends_on = [
    null_resource.invalid_sha_sig
  ]
}

#TODO: Create issue for `terraform.io/builtin/test`. Both assertions pass when not equal
resource "test_assertions" "request_validator" {
  component = "test_error_handling"

  equal "not_sha_signed" {
    description = "Test sha256 header not signed handling"
    got         = jsondecode(data.local_file.not_sha_signed.content)
    want = {
      errorMessage = {
        isError = true
        type    = "ClientException"
        message = "Signature not signed with sha256 (e.g. sha256=123456)"
      }
    }
  }

  equal "invalid_sha_sig" {
    description = "Test invalid sha256 header handling"
    got         = jsondecode(data.local_file.invalid_sha_sig.content)
    want = {
      errorMessage = {
        isError = true
        type    = "ClientException"
        message = "Header signature and expected signature do not match"
      }
    }
  }
  depends_on = [
    null_resource.not_sha_signed,
    null_resource.invalid_sha_sig
  ]
}