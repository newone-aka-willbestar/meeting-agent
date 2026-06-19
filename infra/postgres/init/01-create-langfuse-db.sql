-- 这个脚本只在 postgres 数据卷「第一次初始化」时自动执行
-- （挂在容器的 /docker-entrypoint-initdb.d/ 目录里）。
-- 作用：在同一个 Postgres 实例里，额外建一个给 Langfuse 用的库，
-- 这样应用数据（meeting 库）和可观测数据（langfuse 库）互不污染，
-- 又不用多起一个 Postgres 容器。
CREATE DATABASE langfuse;
