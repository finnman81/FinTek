output "alb_dns_name" {
  value       = aws_lb.main.dns_name
  description = "ALB public DNS name"
}

output "alb_url" {
  value       = "http://${aws_lb.main.dns_name}"
  description = "ALB HTTP URL"
}

output "rds_endpoint" {
  value       = aws_db_instance.main.endpoint
  description = "RDS instance endpoint (host:port)"
}

output "database_url" {
  value       = "postgresql://${var.db_username}:${var.db_password}@${aws_db_instance.main.endpoint}/anchorpoint"
  sensitive   = true
  description = "Full database connection string"
}

output "s3_bucket_name" {
  value       = aws_s3_bucket.documents.id
  description = "S3 bucket for document storage"
}

output "ecr_repository_url" {
  value       = aws_ecr_repository.api.repository_url
  description = "ECR repository URL for Docker images"
}

output "ecs_cluster_name" {
  value       = aws_ecs_cluster.main.name
  description = "ECS cluster name"
}

output "ecs_api_service_name" {
  value       = aws_ecs_service.api.name
  description = "ECS API service name"
}

output "ecs_worker_service_name" {
  value       = aws_ecs_service.worker.name
  description = "ECS worker service name"
}
