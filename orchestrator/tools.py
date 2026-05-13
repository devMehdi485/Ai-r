"""Définition des outils que le LLM peut invoquer (format function calling)."""

TOOLS: list[dict] = [
    {
        "type": "function",
        "function": {
            "name": "takeoff",
            "description": "Décolle le drone et stabilise à 1 mètre.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "land",
            "description": "Atterrit le drone à l'endroit actuel.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "move",
            "description": "Déplacement relatif en mètres dans le repère du drone.",
            "parameters": {
                "type": "object",
                "properties": {
                    "dx": {"type": "number", "description": "Avant (+) / arrière (-)"},
                    "dy": {"type": "number", "description": "Droite (+) / gauche (-)"},
                    "dz": {"type": "number", "description": "Haut (+) / bas (-)"},
                },
                "required": ["dx", "dy", "dz"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "rotate",
            "description": "Rotation autour du yaw en degrés (+ = horaire).",
            "parameters": {
                "type": "object",
                "properties": {"degrees": {"type": "number"}},
                "required": ["degrees"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "detect",
            "description": "Cherche un objet dans la vue actuelle (label COCO).",
            "parameters": {
                "type": "object",
                "properties": {"label": {"type": "string"}},
                "required": ["label"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "capture_photo",
            "description": "Sauvegarde la frame courante.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "wait",
            "description": "Pause en secondes.",
            "parameters": {
                "type": "object",
                "properties": {"seconds": {"type": "number"}},
                "required": ["seconds"],
            },
        },
    },
]
