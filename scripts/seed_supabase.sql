-- Insertar columnas
INSERT INTO columns (title, "order", created_at, updated_at)
VALUES 
    ('To Do', 1, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('In Progress', 2, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
    ('Done', 3, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

-- Obtener IDs de las columnas insertadas
DO $$
DECLARE
    todo_id integer;
    in_progress_id integer;
    done_id integer;
BEGIN
    SELECT id INTO todo_id FROM columns WHERE title = 'To Do' LIMIT 1;
    SELECT id INTO in_progress_id FROM columns WHERE title = 'In Progress' LIMIT 1;
    SELECT id INTO done_id FROM columns WHERE title = 'Done' LIMIT 1;

    -- Insertar tareas
    INSERT INTO tasks (title, description, column_id, "order", completed, created_at, updated_at)
    VALUES 
        ('Design UI', 'Create mockups', todo_id, 1, false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        ('Setup Database', 'Configure PostgreSQL', in_progress_id, 1, false, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP),
        ('API Development', 'Create endpoints', done_id, 1, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);

    -- Insertar relaciones entre tareas y etiquetas
    INSERT INTO task_labels (task_id, label_id)
    SELECT 
        t.id as task_id,
        l.id as label_id
    FROM tasks t
    CROSS JOIN labels l
    WHERE 
        (t.title = 'Design UI' AND l.text IN ('Design', 'Frontend')) OR
        (t.title = 'Setup Database' AND l.text IN ('Backend', 'Feature')) OR
        (t.title = 'API Development' AND l.text IN ('Backend', 'Documentation'));
END $$; 