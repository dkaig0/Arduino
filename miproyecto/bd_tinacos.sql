-- ============================================================
-- Modelo "Tinacos" adaptado de Oracle SQL Developer Data Modeler
-- a MySQL / MariaDB (phpMyAdmin)
--
-- Cambios respecto al script original de Oracle:
--   VARCHAR2(n CHAR)  ->  VARCHAR(n)
--   Ids tipo DATE     ->  DATETIME(6): fecha y hora de creación del registro,
--                         con microsegundos para que no se repitan si se
--                         crean varios registros el mismo día
--   Rol BLOB          ->  VARCHAR(30)
--   Se agrega ENGINE=InnoDB (necesario para FOREIGN KEY)
--   Orden de creacion segun dependencias: Rol -> Usuario -> Tinaco -> ...
-- ============================================================

-- Si ya tienes la base creada, comenta estas dos lineas y
-- selecciona la base desde el panel izquierdo de phpMyAdmin.
-- CREATE DATABASE IF NOT EXISTS bd DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
-- USE bd;

SET FOREIGN_KEY_CHECKS = 0;
DROP TABLE IF EXISTS Ubicacion, Medicion, Tinaco, Usuario, Rol;
SET FOREIGN_KEY_CHECKS = 1;

-- ------------------------------------------------------------
-- Rol
-- ------------------------------------------------------------
CREATE TABLE Rol (
    Id_rol  INT UNSIGNED NOT NULL AUTO_INCREMENT,
    Rol     VARCHAR(30)  NOT NULL,
    CONSTRAINT Rol_PK PRIMARY KEY (Id_rol)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- Usuario
-- ------------------------------------------------------------
CREATE TABLE Usuario (
    Id_usuario        DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    nombre_usuario    VARCHAR(20)  NOT NULL,
    email_usuario     VARCHAR(30)  NOT NULL,
    password_usuario  VARCHAR(255) NOT NULL,
    Rol_Id_rol        INT UNSIGNED NOT NULL,
    CONSTRAINT Usuario_PK PRIMARY KEY (Id_usuario),
    CONSTRAINT Usuario_email_UK UNIQUE (email_usuario),
    CONSTRAINT Usuario_Rol_FK FOREIGN KEY (Rol_Id_rol)
        REFERENCES Rol (Id_rol)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- Tinaco
-- ------------------------------------------------------------
CREATE TABLE Tinaco (
    Id_Tinaco           DATETIME(6) NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    nombre_tinaco       VARCHAR(15),
    capacidad_tinaco    INT         NOT NULL,
    Usuario_Id_usuario  DATETIME(6) NOT NULL,
    CONSTRAINT Tinaco_PK PRIMARY KEY (Id_Tinaco),
    CONSTRAINT Tinaco_Usuario_FK FOREIGN KEY (Usuario_Id_usuario)
        REFERENCES Usuario (Id_usuario)
        ON UPDATE CASCADE
        ON DELETE RESTRICT
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- Medicion
-- ------------------------------------------------------------
CREATE TABLE Medicion (
    Id_medicion       DATETIME(6)   NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    ph_medicion       DECIMAL(4,2)  NOT NULL,
    agua_medicion     DECIMAL(10,2) NOT NULL,
    fecha_medicion    DATETIME(6)   NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    Tinaco_Id_Tinaco  DATETIME(6)   NOT NULL,
    CONSTRAINT Medicion_PK PRIMARY KEY (Id_medicion),
    CONSTRAINT Medicion_Tinaco_FK FOREIGN KEY (Tinaco_Id_Tinaco)
        REFERENCES Tinaco (Id_Tinaco)
        ON UPDATE CASCADE
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- Ubicacion
-- ------------------------------------------------------------
CREATE TABLE Ubicacion (
    Id_ubicacion      DATETIME(6)  NOT NULL DEFAULT CURRENT_TIMESTAMP(6),
    Region            VARCHAR(42)  NOT NULL,
    Ciudad            VARCHAR(20)  NOT NULL,
    Comuna            VARCHAR(20)  NOT NULL,
    Calle             VARCHAR(50)  NOT NULL,
    Numero            INT          NOT NULL,
    Tinaco_Id_Tinaco  DATETIME(6)  NOT NULL,
    CONSTRAINT Ubicacion_PK PRIMARY KEY (Id_ubicacion),
    CONSTRAINT Ubicacion_Tinaco_FK FOREIGN KEY (Tinaco_Id_Tinaco)
        REFERENCES Tinaco (Id_Tinaco)
        ON UPDATE CASCADE
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- ------------------------------------------------------------
-- Datos ficticios
-- La contraseña del usuario demo es "demo1234", guardada con el
-- hash que genera Django (el login no acepta contraseñas en texto plano).
-- ------------------------------------------------------------
INSERT INTO Rol (Rol) VALUES ('Administrador'), ('Usuario');

INSERT INTO Usuario (Id_usuario, nombre_usuario, email_usuario, password_usuario, Rol_Id_rol) VALUES
    ('2026-08-01 09:00:00.000000', 'demo', 'demo@aquavida.cl',
     'pbkdf2_sha256$1500000$7vGvhvhhUdJlP8qPdyWX1G$Zp/7FzohjYLmo+IMXNaIvznLLk15hnRKAl/18eRja6o=', 1);

INSERT INTO Tinaco (Id_Tinaco, nombre_tinaco, capacidad_tinaco, Usuario_Id_usuario) VALUES
    ('2026-08-01 09:15:00.000000', 'Tinaco Norte',   1100, '2026-08-01 09:00:00.000000'),
    ('2026-08-03 11:40:00.000000', 'Tinaco Sur',      750, '2026-08-01 09:00:00.000000'),
    ('2026-08-05 16:20:00.000000', 'Tinaco Comedor', 1500, '2026-08-01 09:00:00.000000');

INSERT INTO Ubicacion (Id_ubicacion, Region, Ciudad, Comuna, Calle, Numero, Tinaco_Id_Tinaco) VALUES
    ('2026-08-01 09:16:00.000000', 'Metropolitana de Santiago', 'Santiago', 'Providencia', 'Av. Los Leones',      1250, '2026-08-01 09:15:00.000000'),
    ('2026-08-03 11:41:00.000000', 'Metropolitana de Santiago', 'Santiago', 'La Florida',  'Av. Vicuña Mackenna', 7110, '2026-08-03 11:40:00.000000'),
    ('2026-08-05 16:21:00.000000', 'Metropolitana de Santiago', 'Santiago', 'Maipú',       'Av. Pajaritos',       2455, '2026-08-05 16:20:00.000000');

INSERT INTO Medicion (Id_medicion, ph_medicion, agua_medicion, fecha_medicion, Tinaco_Id_Tinaco) VALUES
    -- Tinaco Norte
    ('2026-09-15 16:15:00.000000', 7.40,  980.00, '2026-09-15 16:15:00.000000', '2026-08-01 09:15:00.000000'),
    ('2026-09-16 00:15:00.000000', 7.10,  910.00, '2026-09-16 00:15:00.000000', '2026-08-01 09:15:00.000000'),
    ('2026-09-16 08:15:00.000000', 7.20,  870.00, '2026-09-16 08:15:00.000000', '2026-08-01 09:15:00.000000'),
    -- Tinaco Sur
    ('2026-09-15 16:10:00.000000', 6.40,  700.00, '2026-09-15 16:10:00.000000', '2026-08-03 11:40:00.000000'),
    ('2026-09-16 00:10:00.000000', 6.00,  640.00, '2026-09-16 00:10:00.000000', '2026-08-03 11:40:00.000000'),
    ('2026-09-16 08:10:00.000000', 5.80,  590.00, '2026-09-16 08:10:00.000000', '2026-08-03 11:40:00.000000'),
    -- Tinaco Comedor
    ('2026-09-15 16:05:00.000000', 8.30, 1320.00, '2026-09-15 16:05:00.000000', '2026-08-05 16:20:00.000000'),
    ('2026-09-16 00:05:00.000000', 8.60, 1180.00, '2026-09-16 00:05:00.000000', '2026-08-05 16:20:00.000000'),
    ('2026-09-16 08:05:00.000000', 8.90, 1050.00, '2026-09-16 08:05:00.000000', '2026-08-05 16:20:00.000000');
