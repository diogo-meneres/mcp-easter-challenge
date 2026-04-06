-- ==========================================================================
-- Planning Agent — MySQL Schema (4-Layer Model)
-- ==========================================================================
-- Connection: mysql -u root -p
-- Run this file once to bootstrap the database and all tables.
--
-- Layer 1 — Baseline (write-once after kickoff)
-- Layer 2 — Live WIP state (mutable, indexed)
-- Layer 3 — Event log (append-only)
-- Layer 4 — Computed results (ephemeral + snapshots)
-- ==========================================================================

CREATE DATABASE IF NOT EXISTS `planner`
    DEFAULT CHARACTER SET utf8mb4
    DEFAULT COLLATE utf8mb4_unicode_ci;

USE `planner`;

-- ==========================================================================
--  LAYER 1 — Baseline (write-once, never mutated after kickoff)
-- ==========================================================================

-- Plans: top-level container (one per approved workflow)
CREATE TABLE IF NOT EXISTS `plans` (
    `id`                VARCHAR(32)   NOT NULL,
    `name`              VARCHAR(256)  NOT NULL DEFAULT '',
    `status`            VARCHAR(32)   NOT NULL DEFAULT 'planned',  -- planned, active, completed, cancelled
    `priority`          VARCHAR(32)   NOT NULL DEFAULT 'medium',   -- low, medium, high, critical
    `baseline_start`    DATETIME      NULL,      -- frozen at kickoff
    `baseline_end`      DATETIME      NULL,      -- frozen at kickoff
    `created_at`        DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at`        DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB;

-- Actions: grouping of tasks within a plan (one per action in the workflow)
CREATE TABLE IF NOT EXISTS `actions` (
    `id`                VARCHAR(32)   NOT NULL,  -- UUID (PK)
    `plan_id`           VARCHAR(32)   NOT NULL,
    `action_id`         VARCHAR(64)   NOT NULL DEFAULT '',  -- human-readable: A1, A2
    `name`              VARCHAR(256)  NOT NULL DEFAULT '',
    `owner_department`  VARCHAR(128)  NOT NULL DEFAULT '',
    `seq_order`         INT           NOT NULL DEFAULT 0,
    `status`            VARCHAR(32)   NOT NULL DEFAULT 'pending',  -- pending, in_progress, completed
    `created_at`        DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_actions_plan` (`plan_id`),
    CONSTRAINT `fk_actions_plan` FOREIGN KEY (`plan_id`) REFERENCES `plans` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Tasks: each task has baseline fields (Layer 1) + CPM fields (Layer 2)
CREATE TABLE IF NOT EXISTS `tasks` (
    `id`                VARCHAR(32)   NOT NULL,  -- UUID (PK)
    `plan_id`           VARCHAR(32)   NOT NULL,
    `action_id`         VARCHAR(32)   NOT NULL,  -- FK to actions.id (UUID)
    `task_id`           VARCHAR(64)   NOT NULL DEFAULT '',  -- human-readable: T1_1, T1_2
    `description`       TEXT          NOT NULL,
    `owner_role`        VARCHAR(128)  NOT NULL DEFAULT '',
    `status`            VARCHAR(32)   NOT NULL DEFAULT 'pending',  -- pending, in_progress, completed, failed, blocked, cancelled

    -- Layer 1: baseline (frozen at kickoff, never updated)
    `duration_h`        DOUBLE        NOT NULL DEFAULT 0,
    `baseline_start`    DATETIME      NULL,
    `baseline_end`      DATETIME      NULL,
    `baseline_dur_h`    DOUBLE        NOT NULL DEFAULT 0,

    -- Layer 2: CPM live schedule (recomputed on every change)
    `es`                DATETIME      NULL,      -- earliest start
    `ef`                DATETIME      NULL,      -- earliest finish
    `ls`                DATETIME      NULL,      -- latest start
    `lf`                DATETIME      NULL,      -- latest finish
    `total_float_h`     DOUBLE        NOT NULL DEFAULT 0,
    `is_critical`       TINYINT(1)    NOT NULL DEFAULT 0,

    `created_at`        DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at`        DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    PRIMARY KEY (`id`),
    INDEX `idx_tasks_plan` (`plan_id`),
    INDEX `idx_tasks_action` (`action_id`),
    INDEX `idx_tasks_critical` (`is_critical`, `total_float_h`),
    CONSTRAINT `fk_tasks_plan` FOREIGN KEY (`plan_id`) REFERENCES `plans` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_tasks_action` FOREIGN KEY (`action_id`) REFERENCES `actions` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB;

-- Task dependencies: predecessor → successor relationships for CPM graph
CREATE TABLE IF NOT EXISTS `task_dependencies` (
    `id`              VARCHAR(32)   NOT NULL,
    `plan_id`         VARCHAR(32)   NOT NULL,
    `from_task_id`    VARCHAR(32)   NOT NULL,  -- predecessor (FK to tasks.id)
    `to_task_id`      VARCHAR(32)   NOT NULL,  -- successor (FK to tasks.id)
    `lag_h`           DOUBLE        NOT NULL DEFAULT 0,  -- optional delay between tasks
    PRIMARY KEY (`id`),
    INDEX `idx_deps_plan` (`plan_id`),
    INDEX `idx_deps_from` (`from_task_id`),
    INDEX `idx_deps_to` (`to_task_id`),
    CONSTRAINT `fk_deps_plan` FOREIGN KEY (`plan_id`) REFERENCES `plans` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_deps_from` FOREIGN KEY (`from_task_id`) REFERENCES `tasks` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_deps_to` FOREIGN KEY (`to_task_id`) REFERENCES `tasks` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB;


-- --------------------------------------------------------------------------
--  Resources (system-wide registry — must be created before assignments/calendar)
-- --------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS `resources` (
    `id`                      VARCHAR(32)   NOT NULL,
    `name`                    VARCHAR(256)  NOT NULL,
    `type`                    VARCHAR(32)   NOT NULL DEFAULT 'human',
    `department`              VARCHAR(128)  NOT NULL DEFAULT '',
    `role`                    VARCHAR(128)  NOT NULL DEFAULT '',
    `capacity_hours_per_day`  DOUBLE        NOT NULL DEFAULT 8.0,
    `availability`            VARCHAR(256)  NOT NULL DEFAULT 'Mon-Fri 09:00-17:00',
    `active`                  TINYINT(1)    NOT NULL DEFAULT 1,
    `created_at`              DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at`              DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`)
) ENGINE=InnoDB;


-- ==========================================================================
--  LAYER 2 — Live WIP state (mutable, indexed)
-- ==========================================================================

-- Assignments: task ↔ resource relationship (live schedule)
CREATE TABLE IF NOT EXISTS `assignments` (
    `id`              VARCHAR(32)   NOT NULL,
    `plan_id`         VARCHAR(32)   NOT NULL,
    `task_id`         VARCHAR(32)   NOT NULL,  -- FK to tasks.id
    `resource_id`     VARCHAR(32)   NOT NULL,
    `start`           DATETIME      NULL,
    `end`             DATETIME      NULL,
    `created_at`      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `updated_at`      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_assign_plan` (`plan_id`),
    INDEX `idx_assign_task` (`task_id`),
    INDEX `idx_assign_resource` (`resource_id`),
    CONSTRAINT `fk_assign_plan` FOREIGN KEY (`plan_id`) REFERENCES `plans` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_assign_task` FOREIGN KEY (`task_id`) REFERENCES `tasks` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_assign_resource` FOREIGN KEY (`resource_id`) REFERENCES `resources` (`id`)
) ENGINE=InnoDB;

-- Resource calendar: per-resource, per-date availability (overrides default schedule)
CREATE TABLE IF NOT EXISTS `resource_calendar` (
    `id`              VARCHAR(32)   NOT NULL,
    `resource_id`     VARCHAR(32)   NOT NULL,
    `date`            DATE          NOT NULL,
    `available_h`     DOUBLE        NOT NULL DEFAULT 8.0,
    `slot_type`       VARCHAR(32)   NOT NULL DEFAULT 'working',  -- working, holiday, sick, partial
    PRIMARY KEY (`id`),
    UNIQUE INDEX `idx_cal_resource_date` (`resource_id`, `date`),
    CONSTRAINT `fk_cal_resource` FOREIGN KEY (`resource_id`) REFERENCES `resources` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB;


-- ==========================================================================
--  LAYER 3 — Event log (append-only, immutable)
-- ==========================================================================

CREATE TABLE IF NOT EXISTS `event_log` (
    `id`              VARCHAR(32)   NOT NULL,
    `plan_id`         VARCHAR(32)   NOT NULL,
    `type`            VARCHAR(64)   NOT NULL,   -- task_completed, task_failed, task_delayed, resource_unavailable, priority_change, task_suspended
    `timestamp`       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `source`          VARCHAR(128)  NOT NULL DEFAULT '',
    `classification`  VARCHAR(32)   NULL,        -- informational, impactful, critical (set after triage)
    `payload`         JSON          NULL,         -- event-specific data (flexible schema)
    `processed`       TINYINT(1)    NOT NULL DEFAULT 0,
    `created_at`      DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_event_plan` (`plan_id`),
    INDEX `idx_event_processed` (`processed`),
    INDEX `idx_event_type` (`type`),
    CONSTRAINT `fk_event_plan` FOREIGN KEY (`plan_id`) REFERENCES `plans` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB;


-- ==========================================================================
--  LAYER 4 — Computed results (ephemeral + snapshots)
-- ==========================================================================

-- Replan snapshots: before/after KPIs when a significant event triggers replanning
CREATE TABLE IF NOT EXISTS `replan_snapshots` (
    `id`                  VARCHAR(32)   NOT NULL,
    `plan_id`             VARCHAR(32)   NOT NULL,
    `triggered_by_event`  VARCHAR(32)   NULL,     -- FK to event_log.id
    `option_chosen`       VARCHAR(256)  NOT NULL DEFAULT '',
    `chosen_by`           VARCHAR(64)   NOT NULL DEFAULT '',  -- auto, user
    `before_kpis`         JSON          NOT NULL,  -- {spi, sv_hours, pct_complete, critical_path_float_h, sla_remaining_h, tasks_at_risk}
    `after_kpis`          JSON          NOT NULL,  -- same structure
    `changes_applied`     JSON          NULL,       -- list of changes made
    `created_at`          DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (`id`),
    INDEX `idx_replan_plan` (`plan_id`),
    CONSTRAINT `fk_replan_plan` FOREIGN KEY (`plan_id`) REFERENCES `plans` (`id`) ON DELETE CASCADE,
    CONSTRAINT `fk_replan_event` FOREIGN KEY (`triggered_by_event`) REFERENCES `event_log` (`id`)
) ENGINE=InnoDB;
