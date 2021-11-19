data "aws_s3_bucket" "source" {
  bucket = module.base.codepipeline_bucket
}

/* CodeBuild */
resource "aws_codebuild_project" "codebuild" {
  name          = "${var.app_name}-${var.environment_name}"
  build_timeout = "10"
  service_role  = aws_iam_role.codebuild_role.arn

  artifacts {
    type = "CODEPIPELINE"
  }

  environment {
    compute_type    = "BUILD_GENERAL1_SMALL"
    image           = "aws/codebuild/amazonlinux2-x86_64-standard:3.0"
    type            = "LINUX_CONTAINER"
    privileged_mode = true

    environment_variable {
      name  = "ENVIRONMENT_NAME"
      value = var.environment_name
    }

    environment_variable {
      name  = "APP_NAME"
      value = var.app_name
    }

    environment_variable {
      name  = "AWS_REGION"
      value = var.aws_region
    }

    environment_variable {
      name  = "AWS_ACCOUNT_ID"
      value = data.aws_caller_identity.current.id
    }

    environment_variable {
      name  = "APP_URL"
      value = module.loadbalancer.record_fqdn
    }

    /* Repository URIs */
    dynamic "environment_variable" {
      for_each = module.ecs.repository_urls

      content {
        name  = "REPOSITORY_URI_${index(module.ecs.repository_urls, environment_variable.value)}"
        value = environment_variable.value
      }
    }

    /* Container names */
    dynamic "environment_variable" {
      for_each = var.container_names

      content {
        name  = "CONTAINER_NAME_${index(var.container_names, environment_variable.value)}"
        value = environment_variable.value
      }
    }

    /* Container ports */
    dynamic "environment_variable" {
      for_each = var.container_ports

      content {
        name  = "CONTAINER_PORT_${index(var.container_ports, environment_variable.value)}"
        value = environment_variable.value
      }
    }
  }

  source {
    type      = "CODEPIPELINE"
    buildspec = "buildspec.yml"
  }

  tags = local.common_tags
}

/* CodePipeline */
resource "aws_codepipeline" "codepipeline" {
  name     = "${var.app_name}-${var.environment_name}"
  role_arn = aws_iam_role.codepipeline_role.arn

  artifact_store {
    location = data.aws_s3_bucket.source.bucket
    type     = "S3"
  }

  stage {
    name = "Source"

    action {
      name             = "Source"
      category         = "Source"
      owner            = "ThirdParty"
      provider         = "GitHub"
      version          = "1"
      output_artifacts = ["source"]

      configuration = {
        Owner                = local.repository.organization
        Repo                 = local.repository.repo_name
        Branch               = local.repository.branch
        OAuthToken           = var.github_token
        PollForSourceChanges = "false"
      }
    }
  }

  stage {
    name = "Build"

    action {
      name             = "Build"
      category         = "Build"
      owner            = "AWS"
      provider         = "CodeBuild"
      version          = "1"
      input_artifacts  = ["source"]
      output_artifacts = ["imagedefinitions"]

      configuration = {
        ProjectName = aws_codebuild_project.codebuild.name
      }
    }
  }

  stage {
    name = "Deploy"

    action {
      name            = "Deploy"
      category        = "Deploy"
      owner           = "AWS"
      provider        = "ECS"
      input_artifacts = ["imagedefinitions"]
      version         = "1"

      configuration = {
        ClusterName = local.cluster_name
        ServiceName = module.ecs.ecs_service_name
        FileName    = "imagedefinitions.json"
      }
    }
  }

  tags = local.common_tags
}

/* Webhook */
resource "aws_codepipeline_webhook" "codepipeline_webhook" {
  name            = "${var.app_name}-${var.environment_name}-webhook"
  authentication  = "GITHUB_HMAC"
  target_action   = "Source"
  target_pipeline = aws_codepipeline.codepipeline.name

  authentication_configuration {
    secret_token = var.github_token
  }

  filter {
    json_path    = "$.ref"
    match_equals = "refs/heads/${var.environment_name}"
  }
}

resource "github_repository_webhook" "repository_webhook" {
  repository = var.app_name

  configuration {
    url          = aws_codepipeline_webhook.codepipeline_webhook.url
    content_type = "json"
    insecure_ssl = true
    secret       = var.github_token
  }

  events = ["push"]
}
