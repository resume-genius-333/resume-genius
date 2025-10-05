terraform {
  # Require Terraform CLI 1.6 or newer so we have access to the language features and
  # provider behaviors this configuration depends on. Older versions abort early.
  required_version = ">= 1.6.0"

  required_providers {
    aws = {
      # HashiCorp publishes the official AWS provider; pinning the source prevents
      # Terraform from accidentally downloading a forked implementation.
      source = "hashicorp/aws"
      # The pessimistic version constraint allows any 5.x release, receiving bug fixes
      # while avoiding the breaking changes that typically accompany major version bumps.
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.5"
    }
  }

  backend "s3" {
    # Centralised S3 bucket where Terraform keeps the remote state file so every
    # teammate reads and writes the same infrastructure record.
    bucket = "resume-genius-tf-state-ap-sg"
    # Object key (path inside the bucket) that separates this environment's state
    # from other projects and stages.
    key = "resume-genius/litellm/dev.tfstate"
    # Region that hosts both the S3 bucket and the DynamoDB lock table; Terraform will
    # make API calls against this region when storing state.
    region = "ap-southeast-1"
    # DynamoDB table used to acquire a state lock, preventing parallel plans or applies
    # from corrupting the shared state file.
    dynamodb_table = "resume-genius-tf-lock-ap-sg"
    # Enforce server-side encryption so the state file (which may contain secret data)
    # is protected at rest in AWS.
    encrypt = true
  }
}

# Configure the global AWS provider that modules use; the selected region controls where
# all regional resources are created unless a module overrides it.
provider "aws" {
  # The region value comes from the environment's variables to keep geography flexible.
  region = var.aws_region
}
