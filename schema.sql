
            DROP TABLE IF EXISTS teams;
            DROP TABLE IF EXISTS members;

            CREATE TABLE teams (
                team_id INTEGER PRIMARY KEY AUTOINCREMENT,
                team_name TEXT NOT NULL,
                max_members INTEGER NOT NULL DEFAULT 8
            );

            CREATE TABLE members (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                gender TEXT NOT NULL,
                phone TEXT NOT NULL,
                team_id INTEGER NOT NULL,
                is_captain INTEGER NOT NULL DEFAULT 0,
                register_time TEXT NOT NULL,
                FOREIGN KEY (team_id) REFERENCES teams (team_id)
            );

            -- 初始化14个组
            INSERT INTO teams (team_name, max_members) VALUES
                ('A', 8), ('B', 8), ('C', 8), ('D', 8), ('E', 8), ('F', 8), ('G', 8),
                ('H', 8), ('I', 8), ('J', 8), ('K', 8), ('L', 8), ('M', 8), ('N', 8);
            