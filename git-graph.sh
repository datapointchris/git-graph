
# Delete git repo
rm -rf .git

# Create new git repo
git init
touch __init__.py
echo "__version__ = 'v0.1.0'" > __init__.py
git add -A
git commit -m 'feature: Initial Project'
git checkout -b develop

        # Create new feature branch
        git checkout -b feature/Create-Python-Package 

        # Add commits

echo "Sandoval" >> specs.py
echo "Include bill two attorney member common." >> specs.py
echo " " >> specs.py
git add -A
git commit -m "build: feature/Create-Python-Package -- START FEATURE"


echo "Edwards" >> specs.py
echo "Measure surface indeed firm defense miss." >> specs.py
echo " " >> specs.py
git add -A
git commit -m "refactor: feature/Create-Python-Package -- Update code"

echo "Rosario" >> specs.py
echo "Method east somebody also." >> specs.py
echo " " >> specs.py
git add -A
git commit -m "feature: feature/Create-Python-Package -- Fuck Up code"

echo "Cole" >> specs.py
echo "Edge spend change conference." >> specs.py
echo " " >> specs.py
git add -A
git commit -m "feature: feature/Create-Python-Package -- Update code"

echo "Gates" >> specs.py
echo "According mission mean region certain travel." >> specs.py
echo " " >> specs.py
git add -A
git commit -m "feature: feature/Create-Python-Package -- Add code"


        # Merge Branch
        git checkout develop
        git merge --no-edit --no-ff --commit feature/Create-Python-Package

        # Create a Release

# Create a release from base to target
git checkout develop
git checkout -b release/v0.2.0/Create-Python-Package
echo "__version__ = 'v0.2.0'" > __init__.py
git add -A
git commit -m "release: v0.2.0 - Create-Python-Package"
git checkout master
git merge --no-edit --no-ff --commit release/v0.2.0/Create-Python-Package
git tag "v0.2.0"
git checkout develop
git merge master
git branch -d release/v0.2.0/Create-Python-Package


        # Delete Branch
        git branch -d feature/Create-Python-Package

        # Start a long feature
        git checkout -b long-feature/Upgrade-Testing

        
echo "Parker" >> specs.py
echo "Pay push usually bill soon glass." >> specs.py
echo " " >> specs.py
git add -A
git commit -m "feature: long-feature/Upgrade-Testing -- START LONG FEATURE"

        
echo "Morris" >> specs.py
echo "Man try drive individual money from society citizen." >> specs.py
echo " " >> specs.py
git add -A
git commit -m "feature: long-feature/Upgrade-Testing -- Add code"

        
        # Create new feature branch
        git checkout -b feature/Proto 

        # Add commits

echo "Brady" >> specs.py
echo "Act wind particular class." >> specs.py
echo " " >> specs.py
git add -A
git commit -m "performance: feature/Proto -- START FEATURE"


echo "Reynolds" >> specs.py
echo "Pm claim least huge." >> specs.py
echo " " >> specs.py
git add -A
git commit -m "ops: feature/Proto -- Add code"

echo "Leonard" >> specs.py
echo "Official cost close process turn upon capital knowledge." >> specs.py
echo " " >> specs.py
git add -A
git commit -m "wip: feature/Proto -- Update code"

echo "Taylor" >> specs.py
echo "Speak minute whose movie condition leave watch." >> specs.py
echo " " >> specs.py
git add -A
git commit -m "chore: feature/Proto -- Add code"

echo "Meyer" >> specs.py
echo "The economic fear church relationship would door huge." >> specs.py
echo " " >> specs.py
git add -A
git commit -m "feature: feature/Proto -- Fuck Up code"

echo "Lang" >> specs.py
echo "West style size policy." >> specs.py
echo " " >> specs.py
git add -A
git commit -m "feature: feature/Proto -- Add code"


        # Merge Branch
        git checkout develop
        git merge --no-edit --no-ff --commit feature/Proto

        # Create a Release

# Create a release from base to target
git checkout develop
git checkout -b release/v0.3.0/Proto
echo "__version__ = 'v0.3.0'" > __init__.py
git add -A
git commit -m "release: v0.3.0 - Proto"
git checkout master
git merge --no-edit --no-ff --commit release/v0.3.0/Proto
git tag "v0.3.0"
git checkout develop
git merge master
git branch -d release/v0.3.0/Proto


        # Delete Branch
        git branch -d feature/Proto

        git checkout develop
        git merge --no-edit --no-ff --commit develop
        
        
echo "Hutchinson" >> specs.py
echo "Family present fast become natural month travel." >> specs.py
echo " " >> specs.py
git add -A
git commit -m "chore: long-feature/Upgrade-Testing -- RESUME LONG FEATURE Upgrade-Testing"

        
echo "Miller" >> specs.py
echo "Hit detail law design career." >> specs.py
echo " " >> specs.py
git add -A
git commit -m "feature: long-feature/Upgrade-Testing -- Update code"

        
        # Create new feature branch
        git checkout -b feature/MVP 

        # Add commits

echo "Brown" >> specs.py
echo "Man choose me source son budget." >> specs.py
echo " " >> specs.py
git add -A
git commit -m "chore: feature/MVP -- START FEATURE"


echo "Silva" >> specs.py
echo "East consider subject range mind." >> specs.py
echo " " >> specs.py
git add -A
git commit -m "test: feature/MVP -- Delete code"

echo "Roberson" >> specs.py
echo "Home maybe national wall." >> specs.py
echo " " >> specs.py
git add -A
git commit -m "feature: feature/MVP -- Add code"

echo "Harding" >> specs.py
echo "Push term law ground stuff rate." >> specs.py
echo " " >> specs.py
git add -A
git commit -m "feature: feature/MVP -- Update code"

echo "Kennedy" >> specs.py
echo "Group child road dinner professional." >> specs.py
echo " " >> specs.py
git add -A
git commit -m "docs: feature/MVP -- Update code"


        # Merge Branch
        git checkout develop
        git merge --no-edit --no-ff --commit feature/MVP

        # Create a Release

# Create a release from base to target
git checkout develop
git checkout -b release/v0.3.1/MVP
echo "__version__ = 'v0.3.1'" > __init__.py
git add -A
git commit -m "release: v0.3.1 - MVP"
git checkout master
git merge --no-edit --no-ff --commit release/v0.3.1/MVP
git tag "v0.3.1"
git checkout develop
git merge master
git branch -d release/v0.3.1/MVP


        # Delete Branch
        git branch -d feature/MVP

        git checkout develop
        git merge --no-edit --no-ff --commit develop
        
        
echo "Hutchinson" >> specs.py
echo "Family present fast become natural month travel." >> specs.py
echo " " >> specs.py
git add -A
git commit -m "chore: long-feature/Upgrade-Testing -- RESUME LONG FEATURE Upgrade-Testing"

        
echo "Miller" >> specs.py
echo "Hit detail law design career." >> specs.py
echo " " >> specs.py
git add -A
git commit -m "feature: long-feature/Upgrade-Testing -- Update code"

                
        git checkout develop
        git merge --no-edit --no-ff --commit long-feature/Upgrade-Testing
        git branch -d long-feature/Upgrade-Testing
        # Create a Release
        
# Create a release from base to target
git checkout develop
git checkout -b release/v0.4.0/Upgrade-Testing
echo "__version__ = 'v0.4.0'" > __init__.py
git add -A
git commit -m "release: v0.4.0 - Upgrade-Testing"
git checkout master
git merge --no-edit --no-ff --commit release/v0.4.0/Upgrade-Testing
git tag "v0.4.0"
git checkout develop
git merge master
git branch -d release/v0.4.0/Upgrade-Testing

        
        # Create new feature branch
        git checkout -b feature/Integration-Test 

        # Add commits

echo "Young" >> specs.py
echo "Behind cost head ten." >> specs.py
echo " " >> specs.py
git add -A
git commit -m "test: feature/Integration-Test -- START FEATURE"


echo "Potts" >> specs.py
echo "Already movement which." >> specs.py
echo " " >> specs.py
git add -A
git commit -m "docs: feature/Integration-Test -- Delete code"

echo "Swanson" >> specs.py
echo "Two from fall trouble." >> specs.py
echo " " >> specs.py
git add -A
git commit -m "feature: feature/Integration-Test -- Bastardize code"

echo "Webb" >> specs.py
echo "Stand usually since." >> specs.py
echo " " >> specs.py
git add -A
git commit -m "feature: feature/Integration-Test -- Add code"

echo "Mullen" >> specs.py
echo "Area later system many customer." >> specs.py
echo " " >> specs.py
git add -A
git commit -m "refactor: feature/Integration-Test -- Bastardize code"

echo "Richardson" >> specs.py
echo "Level arrive argue huge ball situation." >> specs.py
echo " " >> specs.py
git add -A
git commit -m "test: feature/Integration-Test -- Bastardize code"


        # Merge Branch
        git checkout develop
        git merge --no-edit --no-ff --commit feature/Integration-Test

        # Create a Release

# Create a release from base to target
git checkout develop
git checkout -b release/v1.0.0/Integration-Test
echo "__version__ = 'v1.0.0'" > __init__.py
git add -A
git commit -m "release: v1.0.0 - Integration-Test"
git checkout master
git merge --no-edit --no-ff --commit release/v1.0.0/Integration-Test
git tag "v1.0.0"
git checkout develop
git merge master
git branch -d release/v1.0.0/Integration-Test


        # Delete Branch
        git branch -d feature/Integration-Test

        # Create new feature branch
        git checkout -b feature/Update-CSS 

        # Add commits

echo "Hunt" >> specs.py
echo "Series remain window fly." >> specs.py
echo " " >> specs.py
git add -A
git commit -m "chore: feature/Update-CSS -- START FEATURE"


echo "Harrington" >> specs.py
echo "Help inside operation until physical exist." >> specs.py
echo " " >> specs.py
git add -A
git commit -m "bugfix: feature/Update-CSS -- Delete code"

echo "Reed" >> specs.py
echo "Education care professional." >> specs.py
echo " " >> specs.py
git add -A
git commit -m "feature: feature/Update-CSS -- Modify code"

echo "Baker" >> specs.py
echo "Sign almost task scene begin environmental usually." >> specs.py
echo " " >> specs.py
git add -A
git commit -m "feature: feature/Update-CSS -- Add code"


        # Merge Branch
        git checkout develop
        git merge --no-edit --no-ff --commit feature/Update-CSS

        # Create a Release

# Create a release from base to target
git checkout develop
git checkout -b release/v1.1.0/Update-CSS
echo "__version__ = 'v1.1.0'" > __init__.py
git add -A
git commit -m "release: v1.1.0 - Update-CSS"
git checkout master
git merge --no-edit --no-ff --commit release/v1.1.0/Update-CSS
git tag "v1.1.0"
git checkout develop
git merge master
git branch -d release/v1.1.0/Update-CSS


        # Delete Branch
        git branch -d feature/Update-CSS

        # Start a long feature
        git checkout -b long-feature/NGINX

        
echo "Ramirez" >> specs.py
echo "Support history city room play." >> specs.py
echo " " >> specs.py
git add -A
git commit -m "test: long-feature/NGINX -- START LONG FEATURE"

        
echo "Randall" >> specs.py
echo "Phone mother large according blood general like." >> specs.py
echo " " >> specs.py
git add -A
git commit -m "feature: long-feature/NGINX -- Add code"

        
        # Create new feature branch
        git checkout -b feature/Proto 

        # Add commits

echo "Rodriguez" >> specs.py
echo "Arrive score prevent why four." >> specs.py
echo " " >> specs.py
git add -A
git commit -m "feature: feature/Proto -- START FEATURE"


echo "Jones" >> specs.py
echo "Debate drop personal thank defense." >> specs.py
echo " " >> specs.py
git add -A
git commit -m "docs: feature/Proto -- Fuck Up code"

echo "Allen" >> specs.py
echo "Want area society learn majority full other five." >> specs.py
echo " " >> specs.py
git add -A
git commit -m "feature: feature/Proto -- Bastardize code"

echo "Bryant" >> specs.py
echo "Class again left thing with leg anything." >> specs.py
echo " " >> specs.py
git add -A
git commit -m "test: feature/Proto -- Bastardize code"

echo "Hernandez" >> specs.py
echo "Amount drug feeling draw sport current." >> specs.py
echo " " >> specs.py
git add -A
git commit -m "wip: feature/Proto -- Bastardize code"

echo "Shannon" >> specs.py
echo "Television discover during sure clearly case." >> specs.py
echo " " >> specs.py
git add -A
git commit -m "feature: feature/Proto -- Bastardize code"


        # Merge Branch
        git checkout develop
        git merge --no-edit --no-ff --commit feature/Proto

        # Create a Release

# Create a release from base to target
git checkout develop
git checkout -b release/v1.1.1/Proto
echo "__version__ = 'v1.1.1'" > __init__.py
git add -A
git commit -m "release: v1.1.1 - Proto"
git checkout master
git merge --no-edit --no-ff --commit release/v1.1.1/Proto
git tag "v1.1.1"
git checkout develop
git merge master
git branch -d release/v1.1.1/Proto


        # Delete Branch
        git branch -d feature/Proto

        git checkout develop
        git merge --no-edit --no-ff --commit develop
        
        
echo "Benitez" >> specs.py
echo "Production measure record." >> specs.py
echo " " >> specs.py
git add -A
git commit -m "feature: long-feature/NGINX -- RESUME LONG FEATURE NGINX"

        
echo "Lamb" >> specs.py
echo "Character your commercial picture option likely." >> specs.py
echo " " >> specs.py
git add -A
git commit -m "feature: long-feature/NGINX -- Bastardize code"

        
        # Create new feature branch
        git checkout -b feature/MVP 

        # Add commits

echo "Johnson" >> specs.py
echo "Begin interest drive up shoulder." >> specs.py
echo " " >> specs.py
git add -A
git commit -m "ops: feature/MVP -- START FEATURE"


echo "Wallace" >> specs.py
echo "Gun people indicate." >> specs.py
echo " " >> specs.py
git add -A
git commit -m "wip: feature/MVP -- Modify code"

echo "Oconnor" >> specs.py
echo "Material pull believe find whole success growth body." >> specs.py
echo " " >> specs.py
git add -A
git commit -m "test: feature/MVP -- Fuck Up code"

echo "Richardson" >> specs.py
echo "Congress far husband establish success local." >> specs.py
echo " " >> specs.py
git add -A
git commit -m "feature: feature/MVP -- Modify code"

echo "Allen" >> specs.py
echo "Way around series various can." >> specs.py
echo " " >> specs.py
git add -A
git commit -m "feature: feature/MVP -- Update code"

echo "Bridges" >> specs.py
echo "Fight end or question." >> specs.py
echo " " >> specs.py
git add -A
git commit -m "refactor: feature/MVP -- Add code"


        # Merge Branch
        git checkout develop
        git merge --no-edit --no-ff --commit feature/MVP

        # Create a Release

# Create a release from base to target
git checkout develop
git checkout -b release/v1.2.0/MVP
echo "__version__ = 'v1.2.0'" > __init__.py
git add -A
git commit -m "release: v1.2.0 - MVP"
git checkout master
git merge --no-edit --no-ff --commit release/v1.2.0/MVP
git tag "v1.2.0"
git checkout develop
git merge master
git branch -d release/v1.2.0/MVP


        # Delete Branch
        git branch -d feature/MVP

        git checkout develop
        git merge --no-edit --no-ff --commit develop
        
        
echo "Benitez" >> specs.py
echo "Production measure record." >> specs.py
echo " " >> specs.py
git add -A
git commit -m "feature: long-feature/NGINX -- RESUME LONG FEATURE NGINX"

        
echo "Lamb" >> specs.py
echo "Character your commercial picture option likely." >> specs.py
echo " " >> specs.py
git add -A
git commit -m "feature: long-feature/NGINX -- Bastardize code"

                
        git checkout develop
        git merge --no-edit --no-ff --commit long-feature/NGINX
        git branch -d long-feature/NGINX
        # Create a Release
        
# Create a release from base to target
git checkout develop
git checkout -b release/v1.3.0/NGINX
echo "__version__ = 'v1.3.0'" > __init__.py
git add -A
git commit -m "release: v1.3.0 - NGINX"
git checkout master
git merge --no-edit --no-ff --commit release/v1.3.0/NGINX
git tag "v1.3.0"
git checkout develop
git merge master
git branch -d release/v1.3.0/NGINX

        
        # Create new feature branch
        git checkout -b feature/Continuous-Development 

        # Add commits

echo "Coleman" >> specs.py
echo "Her indeed out although produce." >> specs.py
echo " " >> specs.py
git add -A
git commit -m "test: feature/Continuous-Development -- START FEATURE"


echo "Merritt" >> specs.py
echo "Choice behind same action." >> specs.py
echo " " >> specs.py
git add -A
git commit -m "chore: feature/Continuous-Development -- Add code"

echo "Schultz" >> specs.py
echo "Thought hand almost couple establish check." >> specs.py
echo " " >> specs.py
git add -A
git commit -m "feature: feature/Continuous-Development -- Fuck Up code"

echo "Cobb" >> specs.py
echo "Cause throughout sport whole family return play." >> specs.py
echo " " >> specs.py
git add -A
git commit -m "ops: feature/Continuous-Development -- Bastardize code"

echo "Olson" >> specs.py
echo "Without break though worry." >> specs.py
echo " " >> specs.py
git add -A
git commit -m "chore: feature/Continuous-Development -- Fuck Up code"

echo "Johnson" >> specs.py
echo "Stuff sing contain vote instead main per." >> specs.py
echo " " >> specs.py
git add -A
git commit -m "build: feature/Continuous-Development -- Add code"


        # Merge Branch
        git checkout develop
        git merge --no-edit --no-ff --commit feature/Continuous-Development

        # Create a Release

# Create a release from base to target
git checkout develop
git checkout -b release/v1.4.0/Continuous-Development
echo "__version__ = 'v1.4.0'" > __init__.py
git add -A
git commit -m "release: v1.4.0 - Continuous-Development"
git checkout master
git merge --no-edit --no-ff --commit release/v1.4.0/Continuous-Development
git tag "v1.4.0"
git checkout develop
git merge master
git branch -d release/v1.4.0/Continuous-Development


        # Delete Branch
        git branch -d feature/Continuous-Development
