USE `planner`;

-- 1. Criar os Recursos (Tu e o Gabriel)
INSERT INTO `resources` (`id`, `name`, `type`, `department`, `role`, `capacity_hours_per_day`) VALUES
('R1', 'Diogo', 'human', 'Engineering', 'Systems Engineer', 8.0),
('R2', 'Gabriel', 'human', 'Data Science', 'AI Engineer', 8.0);

-- 2. Criar o Plano
INSERT INTO `plans` (`id`, `name`, `status`, `baseline_start`, `baseline_end`) VALUES
('PLAN-001', 'MVP Easter Challenge', 'active', '2026-04-07 09:00:00', '2026-04-09 18:00:00');

-- 3. Criar as Ações (As Fases do Projeto)
INSERT INTO `actions` (`id`, `plan_id`, `action_id`, `name`, `seq_order`) VALUES
('ACT-1', 'PLAN-001', 'A1', 'Infraestrutura', 1),
('ACT-2', 'PLAN-001', 'A2', 'Desenvolvimento AI', 2),
('ACT-3', 'PLAN-001', 'A3', 'Testes', 3);

-- 4. Criar as Tarefas
-- T1 e T2 formam um caminho demorado (Crítico). T3 é mais rápido e tem folga (Float).
INSERT INTO `tasks` (`id`, `plan_id`, `action_id`, `task_id`, `description`, `duration_h`, `baseline_dur_h`) VALUES
('TSK-1', 'PLAN-001', 'ACT-1', 'T1', 'Configurar Docker e MySQL', 2.0, 2.0),
('TSK-2', 'PLAN-001', 'ACT-1', 'T2', 'Criar FastMCP Server', 4.0, 4.0),
('TSK-3', 'PLAN-001', 'ACT-2', 'T3', 'Desenvolver Agente LLM', 2.0, 2.0),
('TSK-4', 'PLAN-001', 'ACT-2', 'T4', 'Integrar Tools no Server', 6.0, 6.0),
('TSK-5', 'PLAN-001', 'ACT-3', 'T5', 'Testes End-to-End', 2.0, 2.0);

-- 5. Criar as Dependências (O Grafo para o CPM)
INSERT INTO `task_dependencies` (`id`, `plan_id`, `from_task_id`, `to_task_id`) VALUES
('DEP-1', 'PLAN-001', 'TSK-1', 'TSK-2'),
('DEP-2', 'PLAN-001', 'TSK-1', 'TSK-3'),
('DEP-3', 'PLAN-001', 'TSK-2', 'TSK-4'),
('DEP-4', 'PLAN-001', 'TSK-3', 'TSK-4'),
('DEP-5', 'PLAN-001', 'TSK-4', 'TSK-5');

-- 6. Atribuir Tarefas aos Recursos (Para a Ferramenta de Resources)
INSERT INTO `assignments` (`id`, `plan_id`, `task_id`, `resource_id`, `start`, `end`) VALUES
('ASS-1', 'PLAN-001', 'TSK-1', 'R1', '2026-04-07 09:00:00', '2026-04-07 11:00:00'),
('ASS-2', 'PLAN-001', 'TSK-2', 'R1', '2026-04-07 11:00:00', '2026-04-07 15:00:00'),
('ASS-3', 'PLAN-001', 'TSK-3', 'R2', '2026-04-07 11:00:00', '2026-04-07 13:00:00'),
('ASS-4', 'PLAN-001', 'TSK-4', 'R2', '2026-04-07 15:00:00', '2026-04-07 21:00:00'),
('ASS-5', 'PLAN-001', 'TSK-5', 'R1', '2026-04-08 09:00:00', '2026-04-08 11:00:00');