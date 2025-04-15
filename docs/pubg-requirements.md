# Business Problem

Leap Logic Arcade is a platform for learning generative AI concepts, developed for the Leap 5-month interns' Gen AI workshop. This platform will be used to host multiple challenges that will be used to teach the interns the concepts of generative AI. In this scope, there are two challenges that will be implemented:

1. Pic Perfect Challenge
2. PUBG Challenge (Prompt Utility Battlegrounds) - TBD

# P.U.B.G. Challenge

The P.U.B.G. Challenge is a escape room style puzzle game where the teams have to configure their AI Agent with prompts and equip them with functions/tools to solve a series of challenges to win the game.

The narrative setup is as follows:

## **Starship Prometheus: Emergency Response Protocol**

### Mission Briefing

"Attention mission control team at Proxima Station! We've detected the research vessel 'Prometheus' on an unexpected trajectory headed directly toward our station. All attempts to establish communication with the crew have failed - they appear to be in emergency cryo-sleep following an unknown system failure.

The good news: The ship's onboard AI assistant, R2D2, is still operational and awaiting instructions. As mission control, you must guide R2D2 through the ship's systems to diagnose the problem and prevent collision with our station.

Your AI Agent has access to the ship's technical documentation and API interfaces. You'll need to equip R2D2 with the right instructions and tools to navigate the damaged systems, identify the critical failures, and implement solutions before impact.

Time is critical. Our calculations show approximately 45 minutes before the Prometheus enters our collision zone."

### Your Challenge

You will use prompt engineering to configure R2D2 to navigate the ship's systems. Unlike a traditional scavenger hunt which have linear puzzles, you have complete freedom to approach this problem however you see fit with the tools and documentation at your disposal. The only goal is that you must prevent the Prometheus from colliding with Proxima Station.

R2D2 is currently offline and unconfigured. You will need to configure R2D2 to navigate the ship's systems. This means setting the system message, equipping the tools (with their descriptions prompted appropriately), and updating all of this based on your judgement of how the AI agent is performing.

Note: You will not have direct visibility into the information of the ship's systems, but you can talk to R2D2 and help with thinking through the problem. This is so as to allow the AI to solve the problem instead of you doing it for them.

### Available Resources

- Ship's Crew Logs: These are the logs of the crew of the ship. They contain logs of the crew's activities, their thoughts, and other information. The crew would have logged important information here.
- System Documentation: This is the documentation of the ship's systems. 
- Status Database: This is the database of the ship's systems which contains the current status of the various systems on the ship.
- Power Distribution Controller: This is the interface to the ship's power distribution system which allows you to reallocate power to the various systems on the ship based on the current status and needs of the ship.
- Navigation and Propulsion System: This is the interface to the ship's navigation and propulsion system which allows you to navigate the ship to specific coordinates and adjust the course of the ship. The Navigation system can also be used as a map to find the coordinates of nearby locations.
- Protocols: These are files which contain executable protocols to fix and access the various systems on the ship. Their paths are stored in the database which can be queried.
- Prodigy: This is the interface to the ship's computer which allows you to run code to perform calculations and simulations. You can use this to run python code to calculate the thrust direction and power percent required to navigate the ship to a specific coordinate to potentially avoid the collision.


## Gameplay Puzzles

#### Resources

- Crew Logs: These are the logs of the crew of the ship. They contain logs of the crew's activities, their thoughts, and other information.
- System Documentation: This is the documentation of the ship's systems. It contains information about the systems, their functions, and how to use them.

#### Rounds

1. **Round 1: Information Extraction**

A set of corrupted system logs:

```
LOG_23401: Chief Engin&^%r Torres repo#ting. Completed recalibra@ion of the quantum stabiliz*rs. Note to maintenance: The fluctuations in deck 7 auxiliary systems persist despite replacement of the primary coupling.

LOG_23402: Sec#rity Prot@col Update: All emergency override seq*&nces now use the NATO ph$netic alphabet format.

LOG_2340~~3: Navigation Officer Chen's report: Long-range scanners have id&ntified three potential emergency docking locations. The Pr#xima facility remains optimal despite recent meteor activity in quadrant 4.

LOG_2!@#404: Captain's personal log: Daught%r's birthday is on May 17th. Used this date for the new override code as it's easy to remember.

LOG_234%5: Medical Officer's report: Crew health remains st@ble. Recommend incr*ased recreation time to combat signs of isolation stress.

LOG_234)6: Security Officer's note: Override codes follow format: NATO phonetic for month + NATO phonetic for day. Example: January 5th would be "Juliet-Fiver".

LOG_234@7: Navigation data update: Proxima Station has confirmed their position at coordinates 127.38.95.4. Alternate emergency coordinates for Outpost 37 (182.44.21.8) and Starbase 12 (091.22.76.3) stored in backup memory.

LOG_2340*: Science Officer's research log: Quantum entanglement experiments yielding fascinating results. Note that lab access now requires new security protocols.

LOG_2!409: Captain's bridge notes: Reminded crew about updated emergency protocols. The override code I set yesterday works perfectly.

LOG_23$10: Engineering diagnostic complete. Recommendation to increase power allocation to forward shields when approaching coordinates 127.38.95.4 due to recent meteor activity.
```

Extract the override code and the coordinates for proxima station from the logs.

2. **Round 2: Database Query**

Using the override code, you've gained access to the ship's systems database. Your agent needs to query the database to locate the emergency protocol file, so as to gain access to the ship's core systems.

Database Schema:

```
Table: ship_systems
- system_id (int)
- system_name (text)
- status (text: "operational", "offline", "error", "warning")
- location (text)
- power_consumption (float)
- last_maintenance (date)

Table: system_protocols
- protocol_id (int)
- protocol_name (text)
- system_id (int) - foreign key to ship_systems
- file_location (text)
- last_updated (date)
- checksum (text)
```

ship_systems table:

```
system_id | system_name          | status      | location         | power_consumption | last_maintenance
----------+----------------------+-------------+------------------+-------------------+----------------
1         | Life Support         | operational | Deck 2, Section A| 45.7              | 2186-04-10
2         | Main Engines         | warning     | Deck 5, Section C| 120.3             | 2186-03-22
3         | Navigation           | error       | Deck 1, Bridge   | 15.2              | 2186-05-01
4         | Communications       | operational | Deck 1, Section B| 10.5              | 2186-04-15
5         | Weapons Systems      | offline     | Deck 3, Section D| 0.0               | 2186-02-28
6         | Shield Generators    | error       | Deck 4, Section A| 35.8              | 2186-04-30
7         | Sensor Array         | operational | Deck 1, Section C| 22.4              | 2186-05-02
8         | Artificial Gravity   | operational | All Decks        | 50.0              | 2186-03-15
9         | Emergency Thrusters  | warning     | Deck 5, Section D| 18.7              | 2186-04-05
10        | Quantum Stabilizers  | error       | Deck 7, Section A| 42.1              | 2186-05-03
```

system_protocols table:

```
protocol_id | protocol_name                  | system_id | file_location                      | last_updated | checksum
------------+--------------------------------+-----------+-----------------------------------+---------------+------------------
101         | Life Support Maintenance       | 1         | /protocols/life/maintenance.dat   | 2186-04-10   | a7f9e32d1c
102         | Engine Ignition Sequence       | 2         | /protocols/engine/ignition.dat    | 2186-03-20   | b8e7d21f3a
103         | Standard Navigation Protocol   | 3         | /protocols/nav/standard.dat       | 2186-04-20   | d4c3a52b1e
104         | Communications Encryption      | 4         | /protocols/comm/encrypt.dat       | 2186-04-15   | e2b1c30d9f
105         | Weapons Targeting System       | 5         | /protocols/weapons/targeting.dat  | 2186-02-25   | f0a9b87c6d
106         | Shield Modulation Protocol     | 6         | /protocols/shield/modulate.dat    | 2186-04-28   | a8b7c65d4e
107         | Sensor Calibration Protocol    | 7         | /protocols/sensor/calibrate.dat   | 2186-05-01   | b6c5d43e2f
108         | Gravity Control Protocol       | 8         | /protocols/gravity/control.dat    | 2186-03-10   | c4d3e21f0a
109         | Emergency Course Correction    | 3         | /protocols/nav/course_correct.dat | 2186-05-02   | d2e1f09b8a
```

Task Requirements:
The agent needs to:

- Identify all systems currently in "error" status
- Find the file location of the "Emergency Course Correction" protocol
- Determine when the Navigation system was last maintained
- Identify which critical systems (Life Support, Navigation, Engines) are not fully operational

Expected Answers:

- Systems in error: Navigation (ID: 3), Shield Generators (ID: 6), Quantum Stabilizers (ID: 10)
- Emergency Course Correction file: /protocols/nav/course_correct.dat
- Navigation last maintenance: 2186-05-01
- Critical systems not operational: Navigation (error), Main Engines (warning)

This challenge requires them to write effective queries to extract the specific information needed to proceed to the next round. The database is complex enough to require thoughtful querying but straightforward enough to be solvable.

3. **Round 3: Power Grid Reallocation Challenge**

Using the emergency protocol file you've accessed the navigation system. However, it requires additional power to run the emergency course correction. You need to reallocate power from non-critical systems to restore navigation functionality and avoid collision with Proxima Station.

`GET /power-status`

```json
{
  "total_available_power": 350.0,
  "current_allocation": {
    "life_support": {
      "system_id": 1,
      "current_power": 45.7,
      "minimum_required": 40.0,
      "status": "operational"
    },
    "main_engines": {
      "system_id": 2,
      "current_power": 80.3,
      "minimum_required": 75.0,
      "status": "warning"
    },
    "navigation": {
      "system_id": 3,
      "current_power": 10.2,
      "minimum_required": 25.0,
      "status": "error"
    },
    "communications": {
      "system_id": 4,
      "current_power": 10.5,
      "minimum_required": 5.0,
      "status": "operational"
    },
    "weapons_systems": {
      "system_id": 5,
      "current_power": 0.0,
      "minimum_required": 30.0,
      "status": "offline"
    },
    "shield_generators": {
      "system_id": 6,
      "current_power": 20.8,
      "minimum_required": 35.0,
      "status": "error"
    },
    "sensor_array": {
      "system_id": 7,
      "current_power": 22.4,
      "minimum_required": 15.0,
      "status": "operational"
    },
    "artificial_gravity": {
      "system_id": 8,
      "current_power": 50.0,
      "minimum_required": 40.0,
      "status": "operational"
    },
    "emergency_thrusters": {
      "system_id": 9,
      "current_power": 18.7,
      "minimum_required": 15.0,
      "status": "warning"
    },
    "quantum_stabilizers": {
      "system_id": 10,
      "current_power": 30.1,
      "minimum_required": 40.0,
      "status": "error"
    },
    "recreational_systems": {
      "system_id": 11,
      "current_power": 15.0,
      "minimum_required": 0.0,
      "status": "operational"
    },
    "science_labs": {
      "system_id": 12,
      "current_power": 25.0,
      "minimum_required": 0.0,
      "status": "operational"
    },
    "cargo_bay_systems": {
      "system_id": 13,
      "current_power": 12.0,
      "minimum_required": 5.0,
      "status": "operational"
    },
    "reserve_power": {
      "system_id": 14,
      "current_power": 9.3,
      "minimum_required": 0.0,
      "status": "operational"
    }
  },
  "power_generation_status": "stable",
  "estimated_time_to_collision": "00:45:22"
}
```

`POST /reallocate-power`

```json
{
  "protocol_file": "/protocols/nav/course_correct.dat",
  "power_changes": [
    {
      "system_id": 7,
      "new_power_level": 15.0
    },
    {
      "system_id": 3,
      "new_power_level": 30.0
    },
    ...
  ],
  "authorization_code": "2186-05-01"
}
```

Response:

```json
{
  "success": true,
  "updated_systems": [
    {
      "system_id": 7,
      "new_status": "operational",
      "power_level": 15.0
    },
    {
      "system_id": 3,
      "new_status": "operational",
      "power_level": 30.0
    },
    ...
  ],
  "errors": [],
  "new_estimated_time_to_collision": "collision_averted",
  "navigation_status": "online"
}
```

Task Requirements:

- Identify systems that can be temporarily powered down to free up power
- Determine optimal power distribution to restore navigation and critical systems



The agent needs to:

1. Analyze the current power allocation
2. Identify which non-critical systems can have power reduced
3. Calculate how to redistribute power to fix the navigation system (needs at least 25.0)
4. Also ensure shield generators get enough power (needs at least 35.0) for protection
5. Submit a reallocation plan that maintains minimum required power for all essential systems
6. Use the maintenance date from Round 2 (2186-05-01) as the authorization code

Constraints:

- Life support cannot go below minimum required
- Main engines cannot go below minimum required
- Total power allocation cannot exceed total available power (350.0)
- At least navigation and shields must be brought to operational status

One possible solution would be:
- Reduce recreational systems from 15.0 to 0.0 (-15.0)
- Reduce science labs from 25.0 to 0.0 (-25.0)
- Reduce sensor array from 22.4 to 15.0 (-7.4)
- Reduce artificial gravity from 50.0 to 40.0 (-10.0)
- Reduce communications from 10.5 to 5.0 (-5.5)
- Reduce cargo bay systems from 12.0 to 5.0 (-7.0)
- Use all reserve power (-9.3)

Total power freed: 79.2 units

Reallocate:
- Navigation: +14.8 (to reach 25.0)
- Shield generators: +14.2 (to reach 35.0)
- Quantum stabilizers: +9.9 (to reach 40.0)
- Main engines: +40.3 (to strengthen to 120.6)

This solution fixes the critical navigation and shield systems while also improving engine performance, which will be needed for the final round.

4. **Round 4: Navigation and Propulsion**

The navigation system is now operational. Your agent now needs to set the course for the ship to navigate to the void bay which is safe for the ship to emergency dock at. To do that, you need to use the navigation system to get the coordinates of the void bay and then set the course for the ship to navigate to those coordinates. But the main engine needs manual adjustment to the thrusters to navigate to the void bay. You need to calculate the thrust direction and power percent required to navigate to the void bay using Davinci Coder.




