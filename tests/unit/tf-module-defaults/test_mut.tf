locals {
  mut = basename(path.cwd)
  #TODO: figure out why using random_id causes github webhook resource for_each depedency error
  # repo_name = "mut-${local.mut}-${random_id.this.id}"
  repo_name     = "mut-${local.mut}"
  test_payloads = file("${path.cwd}/test_payloads.json")
}

provider "random" {}

resource "random_id" "this" {
  byte_length = 8
}

resource "github_repository" "test" {
  name        = local.repo_name
  description = "Test repo for mut: ${local.mut}"
  auto_init   = true
  visibility  = "public"
  depends_on = [
    random_id.this
  ]
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
  source = "../..//"
  repos = [
    {
      name = github_repository.test.name
      filter_groups = [
        {
          events = ["push"]
        }
      ]
    }
  ]
}

resource "null_resource" "not_sha_signed" {
  triggers = {
    run = timestamp()
  }
  provisioner "local-exec" {
    command = <<EOF
curl --silent \
  -H 'Content-Type: application/json' \
  -H 'X-Hub-Signature-256:  ${sha256("test")}' \
  -H 'X-GitHub-Event: push' \
  -d '{"text": "foo"}' \
  -o ${path.cwd}/.tmp/not_sha_signed.json \
  ${module.mut_github_webhook_request_validator.invoke_url}
  EOF
  }
}

resource "null_resource" "invalid_sha_sig" {
  triggers = {
    run = timestamp()
  }
  provisioner "local-exec" {
    command = <<EOF
curl --silent \
  -H 'Content-Type: application/json' \
  -H 'X-Hub-Signature-256: sha256=${sha256("test")}' \
  -H 'X-GitHub-Event: push' \
  -d '{"text": "foo"}' \
  -o ${path.cwd}/.tmp/invalid_sha_sig.json \
  ${module.mut_github_webhook_request_validator.invoke_url}
  EOF
  }
}


data "local_file" "not_sha_signed" {
  filename = "${path.cwd}/.tmp/not_sha_signed.json"
  depends_on = [
    null_resource.not_sha_signed
  ]
}

data "local_file" "invalid_sha_sig" {
  filename = "${path.cwd}/.tmp/invalid_sha_sig.json"
  depends_on = [
    null_resource.invalid_sha_sig
  ]
}

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