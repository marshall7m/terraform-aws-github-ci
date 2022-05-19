module "mut_github_webhook_request_validator" {
  source     = "../../../../..//"
  create_api = true
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