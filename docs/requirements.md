# Business Problem

Leap Logic Arcade is a platform for learning generative AI concepts, developed for the Leap 5-month interns' Gen AI workshop. This platform will be used to host multiple challenges that will be used to teach the interns the concepts of generative AI. In this scope, there are two challenges that will be implemented:

1. Pic Perfect Challenge
2. PUBG Challenge (Prompt Utility Battlegrounds) - TBD

## Pic Perfect Challenge

The Logic Arcade project implements the "Pic Perfect Challenge" - an engaging team-based deception game that combines AI image generation with strategic voting.

### Challenge Overview

The Pick Perfect Challenge is a competitive event with the following mechanics:

1. **Image Generation Phase**:

   - Hosts generate two images using the same prompt
   - One image is revealed to all teams (Reference Image)
   - One image is kept hidden (Hidden Original)
   - Teams use AI/image generation tools to create images based on the same prompt
   - The goal is to either:
     a) Create an image very similar to the reference image to deceive other teams
     b) Successfully identify the hidden original image during voting

2. **Voting Phase**:

   - All generated images (including the hidden original) are pooled together
   - Teams can vote for which image they believe is the hidden original
   - Teams cannot vote for their own submissions
   - Each team gets a limited number of votes (3 votes per team)

3. **Scoring System**:
   - Deception Points: 3 points for each vote received from other teams
   - Discovery Points: 10 points for correctly identifying the hidden original image
   - Winner: Team with the highest total points at the end of the round

### Business Goals

1. **Strategic Thinking**: Encourage teams to think strategically about whether to aim for deception or discovery
2. **Creative Competition**: Foster healthy competition through creative use of AI image generation tools
3. **Engagement**: Create an exciting game format that keeps teams engaged through multiple phases
4. **Technical Learning**: Provide hands-on experience with AI image generation tools in a fun, gamified environment
5. **Team Building**: Promote team discussion and collective decision-making during both generation and voting phases

This unique challenge format creates an entertaining blend of creativity, strategy, and deception, while also serving as an innovative way to explore and understand AI image generation capabilities.

### User Flow

The platform follows a structured flow to guide teams through the challenge:

1. **Landing Page**

   - Welcome screen introducing Leap Logic Arcade
   - Option to proceed to team login
   - Information about ongoing challenges

2. **Team Authentication**

   - Login form with:
     - Team Name field
     - Team Secret field
   - Secure authentication to track team progress and submissions

3. **Home Screen / Challenge Dashboard**

   - Rules and Regulations section clearly explaining:
     - Challenge mechanics
     - Scoring system
     - Time limits
     - Submission guidelines
   - Prominently displayed Reference Image (publicly revealed by hosts)
   - Image Submission Section:
     - Image upload capability
     - Prompt input field
     - Submit button (disabled after submission)
     - Preview of submitted image (if already submitted)

4. **Voting Arena**

   - Pool of all submitted images (excluding team's own submission)
   - Hidden original image mixed into the pool
   - Voting Interface:
     - Maximum 3 votes per team
     - Vote counter showing remaining votes
     - Submit vote button
     - Confirmation dialog for votes
   - Time Management:
     - Prominent countdown timer in top right corner
     - Automatic closure of voting at time limit
     - Visual indicators for time remaining

5. **Leaderboard**
   - Real-time updated scoring table showing:
     - Team Name
     - Deception Points (3 points per vote received)
     - Discovery Points (10 points for identifying hidden image)
     - Delusion Points (penalty points if applicable)
     - Total Points (sum of Deception + Discovery - Delusion)
   - Sorting capability by different point categories
   - Visual highlights for top performers

### Navigation Requirements

- Clear navigation between sections
- Disabled access to voting until submission phase is complete
- No access to leaderboard until voting phase is complete
- Ability to return to rules and regulations from any screen

### State Management Requirements

- Persist team login status
- Track submission status
- Track remaining votes
- Handle session timeouts gracefully
- Prevent multiple submissions/votes from same team
