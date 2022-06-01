module "mut_github_webhook_request_validator" {
  source                = "../../../../..//"
  create_api            = false
  includes_private_repo = false
  api_id                = "test-api"
  root_resource_id      = "test-api-root"
  execution_arn         = "arn:aws:execute-api:us-west-2:123456789012:testid"
  repos = [
    {
      name = "user/test-repo"
      filter_groups = [
        [
          {
            type    = "event"
            pattern = "push"
          }
        ]
      ]
    }
  ]
}