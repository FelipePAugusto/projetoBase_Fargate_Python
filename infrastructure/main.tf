provider "aws" {
  region = var.aws_region
}

provider "github" {
  organization = "madeiramadeirabr"
  token        = var.github_token
}

data "aws_caller_identity" "current" {}

module "base" {
  source           = "app.terraform.io/MadeiraMadeira/base/aws"
  version          = "3.0.14"
  environment_name = var.environment_name
}

locals {
  /* ECS */
  cluster_name = module.base.ecs_cluster_name

  /* Github */
  repository = {
    organization = "madeiramadeirabr"
    repo_name    = var.app_name
    branch       = var.environment_name
  }

  /* Tags */
  common_tags = {
    Env = var.environment_name
    App = var.app_name
  }
}

/* ECS (ALB and Autoscaling enabled) */
module "ecs" {
  source  = "app.terraform.io/MadeiraMadeira/ecs/aws"
  version = "3.8.1"

  is_service         = true # 'true' -> Service | 'false' -> Scheduled Task
  has_load_balancer  = true # Nao pode ser 'true' se 'is_service = false'
  enable_autoscaling = true # Nao pode ser 'true' se 'is_service = false'

  environment_name = var.environment_name
  app_name         = var.app_name
  cluster_name     = local.cluster_name

  /* Task Definition */
  container_names           = var.container_names    # ["python"]
  container_ports           = var.container_ports    # [80]
  discovery_container_names = var.container_names    # ["python"]
  discovery_container_ports = var.container_ports    # [80]
  task_definition = {
    launch_type  = "FARGATE"
    memory       = var.container_memory
    cpu          = var.container_cpu
    network_mode = "awsvpc"
  }
  container_definitions_file_path = "${path.module}/assets/containerDefinitions.json"

  /* Network */
  ecs_network_configuration_subnets         = module.base.private_subnet_ids
  ecs_network_configuration_security_groups = module.base.default_private_security_group_ids

  /* Loadbalancer */
  task_desired_count            = var.task_desired_count
  lb_target_group_resource_arns = [aws_lb_target_group.webserver_target_group.arn]
  autoscaling_capacity = {
    min_capacity = var.autoscaling_capacity.min
    max_capacity = var.autoscaling_capacity.max
  }
}
