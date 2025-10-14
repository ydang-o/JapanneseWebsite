from __future__ import annotations
import os
from typing import Dict, Any, List
from flask import Flask
from sqlalchemy import inspect, text
from sqlalchemy.exc import OperationalError
from .extensions import db


_EXPECTED_TABLES = [
    "users",
    "point_transactions",
]


def _mysql_create_database_if_missing(app: Flask) -> bool:
    """Attempt to create MySQL database if it does not exist.
    Returns True if created or already exists; False if not applicable.
    """
    uri = app.config.get("SQLALCHEMY_DATABASE_URI", "")
    if not uri.startswith("mysql+"):
        raise RuntimeError("后端仅允许使用 MySQL 数据库，请检查配置。")

    # Detect unknown database by attempting a lightweight connection
    try:
        with app.app_context():
            conn = db.engine.connect()
            conn.close()
            return True
    except OperationalError as exc:  # type: ignore
        msg = str(exc).lower()
        if "unknown database" not in msg:
            # Not a missing DB case
            return False

    # Create the database using PyMySQL with server-level connection
    import pymysql  # type: ignore

    host = app.config.get("MYSQL_HOST")
    port = int(app.config.get("MYSQL_PORT", 3306))
    user = app.config.get("MYSQL_USER")
    password = app.config.get("MYSQL_PASSWORD")
    dbname = app.config.get("MYSQL_DB")

    connection = pymysql.connect(host=host, port=port, user=user, password=password, autocommit=True)
    try:
        with connection.cursor() as cur:
            cur.execute(
                f"CREATE DATABASE IF NOT EXISTS `{dbname}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"
            )
    finally:
        connection.close()
    return True


def _default_schema_sql(dialect: str) -> str:
    if dialect.startswith("mysql"):
        return (
            """
            CREATE TABLE IF NOT EXISTS `users` (
              `id` INT NOT NULL AUTO_INCREMENT,
              `email` VARCHAR(255) NOT NULL UNIQUE,
              `password_hash` VARCHAR(255) NOT NULL,
              `display_name` VARCHAR(255) NOT NULL DEFAULT 'ユーザー',
              `created_at` DATETIME NULL,
              `points_balance` INT NOT NULL DEFAULT 0,
              `status` VARCHAR(16) NOT NULL DEFAULT 'pending',
              PRIMARY KEY (`id`)
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

            CREATE TABLE IF NOT EXISTS `point_transactions` (
              `id` INT NOT NULL AUTO_INCREMENT,
              `user_id` INT NOT NULL,
              `delta` INT NOT NULL,
              `reason` VARCHAR(255) NOT NULL DEFAULT '調整',
              `created_at` DATETIME NULL,
              PRIMARY KEY (`id`),
              CONSTRAINT `fk_pt_user` FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE CASCADE
            ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
            """
        )
    # sqlite fallback
    return (
        """
        CREATE TABLE IF NOT EXISTS users (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          email TEXT NOT NULL UNIQUE,
          password_hash TEXT NOT NULL,
          display_name TEXT NOT NULL DEFAULT 'ユーザー',
          created_at DATETIME NULL,
          points_balance INTEGER NOT NULL DEFAULT 0,
          status TEXT NOT NULL DEFAULT 'pending'
        );

        CREATE TABLE IF NOT EXISTS point_transactions (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          user_id INTEGER NOT NULL,
          delta INTEGER NOT NULL,
          reason TEXT NOT NULL DEFAULT '調整',
          created_at DATETIME NULL,
          FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
        );
        """
    )


def _execute_sql_script(sql_script: str) -> None:
    # Naive splitter by ';' that's safe enough for our simple DDL
    statements = [stmt.strip() for stmt in sql_script.split(';') if stmt.strip()]
    for stmt in statements:
        db.session.execute(text(stmt))
    db.session.commit()


def _ensure_columns(inspector) -> Dict[str, Any]:
    """Ensure newly added columns exist (idempotent)."""
    results: Dict[str, Any] = {"added_columns": []}
    # users.status
    cols = {c["name"] for c in inspector.get_columns("users")}
    if "status" not in cols:
        driver = db.engine.url.drivername
        if driver.startswith("mysql"):
            db.session.execute(text("ALTER TABLE `users` ADD COLUMN `status` VARCHAR(16) NOT NULL DEFAULT 'pending'"))
        else:
            db.session.execute(text("ALTER TABLE users ADD COLUMN status TEXT NOT NULL DEFAULT 'pending'"))
        db.session.commit()
        results["added_columns"].append("users.status")
    return results


def ensure_database_initialized(app: Flask) -> Dict[str, Any]:
    """Ensure database and required tables exist. Return summary info.
    Order:
      1) For MySQL, create database if missing
      2) Check expected tables with inspector
      3) If missing, try SQLAlchemy create_all()
      4) If still missing, execute built-in SQL DDL (or SCHEMA_SQL_PATH if provided)
      5) Ensure new columns exist (like users.status)
    """
    results: Dict[str, Any] = {"created_database": False, "created_tables": [], "used_fallback_sql": False}

    # Step 1: ensure database exists (MySQL)
    created_db = _mysql_create_database_if_missing(app)
    results["created_database"] = bool(created_db)

    with app.app_context():
        inspector = inspect(db.engine)
        missing: List[str] = [t for t in _EXPECTED_TABLES if not inspector.has_table(t)]
        if not missing:
            # Ensure columns
            col_res = _ensure_columns(inspector)
            results.update(col_res)
            results["missing_tables"] = []
            results["status"] = "ok"
            return results

        # Step 2: try create_all
        db.create_all()

        inspector = inspect(db.engine)
        still_missing: List[str] = [t for t in _EXPECTED_TABLES if not inspector.has_table(t)]
        if not still_missing:
            # Ensure columns
            col_res = _ensure_columns(inspector)
            results.update(col_res)
            results["created_tables"] = missing
            results["missing_tables"] = []
            results["status"] = "created"
            return results

        # Step 3: fallback to SQL script
        sql_path = os.getenv("SCHEMA_SQL_PATH")
        if sql_path and os.path.exists(sql_path):
            with open(sql_path, "r", encoding="utf-8") as f:
                sql_text = f.read()
        else:
        sql_text = _default_schema_sql(db.engine.url.drivername)

        _execute_sql_script(sql_text)

        inspector = inspect(db.engine)
        final_missing: List[str] = [t for t in _EXPECTED_TABLES if not inspector.has_table(t)]
        results["used_fallback_sql"] = True
        # Ensure columns
        col_res = _ensure_columns(inspector)
        results.update(col_res)
        if final_missing:
            results["missing_tables"] = final_missing
            results["status"] = "partial"
        else:
            results["created_tables"] = still_missing
            results["missing_tables"] = []
            results["status"] = "created"
        return results 