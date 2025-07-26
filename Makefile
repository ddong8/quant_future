.PHONY: help install-backend install-frontend install dev-backend dev-frontend dev test-backend test-frontend test lint-backend lint-frontend lint format-backend format-frontend format clean

help: ## 显示帮助信息
	@echo "量化交易平台开发命令："
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install-backend: ## 安装后端依赖
	cd backend && python -m venv venv && source venv/bin/activate && pip install -r requirements.txt

install-frontend: ## 安装前端依赖
	cd frontend && npm install

install: install-backend install-frontend ## 安装所有依赖

dev-backend: ## 启动后端开发服务器
	cd backend && source venv/bin/activate && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

dev-frontend: ## 启动前端开发服务器
	cd frontend && npm run dev

dev: ## 同时启动前后端开发服务器
	make -j2 dev-backend dev-frontend

test-backend: ## 运行后端测试
	cd backend && source venv/bin/activate && pytest

test-frontend: ## 运行前端测试
	cd frontend && npm run test

test: test-backend test-frontend ## 运行所有测试

lint-backend: ## 检查后端代码
	cd backend && source venv/bin/activate && flake8 app/ && mypy app/

lint-frontend: ## 检查前端代码
	cd frontend && npm run lint

lint: lint-backend lint-frontend ## 检查所有代码

format-backend: ## 格式化后端代码
	cd backend && source venv/bin/activate && black app/ && isort app/

format-frontend: ## 格式化前端代码
	cd frontend && npm run format

format: format-backend format-frontend ## 格式化所有代码

clean: ## 清理构建文件
	rm -rf backend/__pycache__/
	rm -rf backend/app/__pycache__/
	rm -rf backend/.pytest_cache/
	rm -rf frontend/node_modules/
	rm -rf frontend/dist/
	find . -name "*.pyc" -delete
	find . -name "__pycache__" -type d -exec rm -rf {} +