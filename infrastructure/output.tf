output "ecr_repository_url" {
  value = module.ecs.repository_urls
}

output "ecs_service_name" {
  value = module.ecs.ecs_service_name
}
