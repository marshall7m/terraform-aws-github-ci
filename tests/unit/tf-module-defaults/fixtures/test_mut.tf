locals {
  mut = basename(path.cwd)
  repo_name     = "mut-${local.mut}"
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

module "mut_github_webhook_request_validator" {
  source = "../..//"
  repos = [
    {
      name = "user/test-repo"
      filter_groups = [
        {
          events = ["push"]
        }
      ]
    }
  ]
}