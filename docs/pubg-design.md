# Technical Design (PUBG Challenge)

## AI Agent Playground

### DynamoDB Tables

**Table: `pubg-agents`**

- teamName (string)
- instructions (string)
- temperature (float)
- tools (array of maps)
- previousResponseId (string)

**AgentsDao**

- get_agent_state(team_name: str) -> dict
- update_agent_config(team_name: str, instructions: str, temperature: float) -> None
- get_agent_tools(team_name: str) -> list[Dict[str, str]]
- add_agent_tool(team_name: str, tool: Dict[str, str]) -> None
- delete_agent_tool(team_name: str, tool_name: str) -> None
- update_previous_response_id(team_name: str, response_id: str) -> None

### APIs

#### PATCH /api/pubg/agent/state

Updates the AI agent state for a team.

**Request Body:**

Fields to update:

- instructions (string)
- temperature (float)
- previousResponseId (string)

```json
Header
team-name: string

Body
{
    "instructions": "string",
    "temperature": 0.0
}
```

**Response:**

```json
{
  "success": true,
  "message": "Agent state updated successfully"
}
```

#### POST /api/pubg/agent/tool

Add a tool to the AI agent.

**Request Body:**

```json
{
  "name": "string",
  "description": "string"
}
```

#### DELETE /api/pubg/agent/tool/{name}

Delete a tool from the AI agent.

**Response:**

```json
{
  "success": true,
  "message": "Tool deleted successfully"
}
```

#### POST /api/pubg/agent/chat/message

Chat with the AI agent.

**Request Body:**

```json
{
  "message": "string"
}
```

**Response:**

```json
{
  "response": "string"
}
```

#### GET /api/pubg/agent/chat/history

Get the chat history for a team.





### Tools

```python
def get_crew_logs():
    return "string"

def get_ship_docs():
    return "string"

def login_to_system(override_key):
    return "string"

def query_status_database(sql_query):
    return "string"

def get_current_power_status():
    return "string"

def update_power_distribution(power_status):
    return "string"

def navigation_system(command):
    case command:
        "get_current_location":
            return get_current_location()
        "get_current_location":
            return get_current_location()

def propulsion_system(command):
    case command:
        "get_current_velocity":
            return get_current_velocity()
        "set_thrust":
            return set_thrust(thrust)
        "get_current_location":
            return get_current_location()



```

## Gameplay

### DynamoDB Tables

**Table: `pubg-game-state`**

- teamName (string)
- systemAccess (bool) - whether the team has access to the system. Use the override key to enable access.
- powerDistribution (maps) - current power distribution of the ship
- isCourseSet (bool) - whether the course is set for the ship to navigate to the target coordinates
- isThrustSet (bool) - whether the thrust is set for the ship to navigate to the target coordinates
- hasCompletedMission (bool) - whether the team has completed the mission
