<?php
return [
    'db_host' => '127.0.0.1',
    'db_port' => 3306,
    'db_name' => 'skillgraph',
    // Default for private local XAMPP installs. Use a local-only account with DB creation rights.
    'db_user' => 'root',
    'db_password' => 'Astha%1049',
    'jwt_secret' => 'qe4kgZO5Th5YhEL4MxgSynvNYF90f/nWNok+TYQax8c=',
    'ai_provider' => '', // optional: openai or openai_compatible
    'ai_api_key' => '',
    'ai_base_url' => 'https://api.openai.com/v1',
    'ai_model' => 'gpt-4o-mini',
];
