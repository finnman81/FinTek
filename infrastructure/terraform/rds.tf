# Single-AZ RDS Postgres for Phase 0. Enable pgvector in a custom parameter group.

resource "aws_db_subnet_group" "main" {
  name       = "${local.name_prefix}-db-subnet"
  subnet_ids = [aws_subnet.public_a.id]

  tags = { Name = "${local.name_prefix}-db-subnet" }
}

resource "aws_db_parameter_group" "main" {
  family = "postgres15"
  name   = "${local.name_prefix}-pg15"

  # pgvector is available in RDS Postgres 15+ via extension; enable in DB after create
  parameter {
    name  = "shared_preload_libraries"
    value = "pg_stat_statements"
  }

  tags = { Name = "${local.name_prefix}-params" }
}

resource "aws_security_group" "rds" {
  name_prefix = "${local.name_prefix}-rds-"
  vpc_id      = aws_vpc.main.id

  ingress {
    from_port   = 5432
    to_port     = 5432
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = { Name = "${local.name_prefix}-rds-sg" }
}

resource "aws_db_instance" "main" {
  identifier     = "${local.name_prefix}-db"
  engine         = "postgres"
  engine_version = "15.4"
  instance_class = "db.t3.small"

  allocated_storage     = 20
  max_allocated_storage = 100
  storage_encrypted     = true

  db_name  = "anchorpoint"
  username = var.db_username
  password = var.db_password

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  parameter_group_name   = aws_db_parameter_group.main.name
  publicly_accessible    = true # Phase 0: simplify; restrict in prod

  skip_final_snapshot = var.environment == "dev"

  tags = { Name = "${local.name_prefix}-db" }
}

# After first apply, run in DB: CREATE EXTENSION IF NOT EXISTS vector;
output "rds_endpoint" {
  value = aws_db_instance.main.endpoint
}

output "database_url" {
  value     = "postgresql://${var.db_username}:${var.db_password}@${aws_db_instance.main.endpoint}/anchorpoint"
  sensitive = true
}
