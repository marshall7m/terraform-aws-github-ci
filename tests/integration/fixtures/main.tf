module "mut_github_webhook_request_validator" {
  source     = "../../..//"
  create_api = true
  repos      = var.repos
}