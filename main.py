import textwrap
from faker import Faker
import random
from pydantic import BaseSettings
import subprocess
import time
import os
from contextlib import contextmanager
import itertools


class Config(BaseSettings):
    release_merge_options: str = ' '.join(['--no-edit', '--no-ff', '--commit'])
    feature_merge_options: str = ' '.join(['--no-edit', '--no-ff', '--commit'])
    long_feature_update_strategy: str = 'merge'
    long_feature_merge_options: str = ' '.join(['--no-edit', '--no-ff', '--commit'])
    inital_version: str = 'v0.1.0'


config = Config()


class GitRepo:
    def __init__(
        self,
        name: str,
        new_dir: bool = False,
        overwrite: bool = True,
        version: tuple[int] = (0, 1, 0),
    ):
        self.name = name
        self.new_dir = new_dir
        self.overwrite = overwrite
        self.major, self.minor, self.patch = version
        self.version = f'v{self.major}.{self.minor}.{self.patch}'

    def bump_version(self, version_type: str) -> None:
        match version_type:
            case 'major':
                self.major += 1
                self.minor = 0
                self.patch = 0
            case 'minor':
                self.minor += 1
                self.patch = 0
            case 'patch':
                self.patch += 1
        self.version = f'v{self.major}.{self.minor}.{self.patch}'

    def init_project(self) -> str:
        return textwrap.dedent(
            f'''
        # Create new git repo
        git init
        touch __init__.py
        echo "__version__ = '{self.version}'" > __init__.py
        git add -A
        git commit -m 'feature: Initial Project'
        git checkout -b develop
        '''
        )

    def delete_repo(self) -> None:
        return textwrap.dedent(
            '''
            # Delete git repo
            rm -rf .git
            '''
        )

    def commit(self, msg: str = '', branch: str = None) -> str:
        """Add text and commit
        Start: current branch
        End: current branch
        """
        verbs = ['Add', 'Update', 'Delete', 'Modify', 'Fuck Up', 'Bastardize']
        commit_message = f"{branch} -- {(msg or f'{random.choice(verbs)} code')}"
        return textwrap.dedent(
            f'''
        echo "{fake.last_name()}" >> specs.py
        echo "{fake.sentence()}" >> specs.py
        echo " " >> specs.py
        git add -A
        git commit -m "{commit_type()}: {commit_message}"
        '''
        )

    def feature(self, feature: str, base_branch: str = '', merge_branch: str = 'develop') -> str:
        """Create a Feature Branch

        Start: Current Branch
        End: `merge_branch` Default: develop

        1. Checkout a new branch
        2. Make some commits
        3. Merge to `merge_branch`, default: 'develop'
        4. Delete branch

        """

        LENGTH_LIMIT = 30
        feature = feature.replace(' ', '-')[:LENGTH_LIMIT]
        this_branch = f'feature/{feature}'

        return textwrap.dedent(
            f'''
        # Create new feature branch
        git checkout -b {this_branch} {base_branch}

        # Add commits
        {self.commit('START FEATURE', this_branch)}
        {''.join(self.commit('', this_branch) for _ in range(random.randint(1, 5)))}

        # Merge Branch
        git checkout {merge_branch}
        git merge {config.feature_merge_options} {this_branch}

        # Create a Release
        {self.release(version_type(), feature)}

        # Delete Branch
        git branch -d {this_branch}
        '''
        )

    # @contextmanager
    def long_feature(
        self, name: str, merge_branch: str = 'develop', short_features: list[str] = ['Proto', 'MVP']
    ) -> str:
        name = name.replace(' ', '-')
        this_branch = f'long-feature/{name}'

        start = f'''
        # Start a long feature
        git checkout -b {this_branch}

        {self.commit(f'START LONG FEATURE', this_branch)}
        {self.commit('', this_branch)}
        '''

        merge_inner_feature = f'''
        git checkout develop
        git {config.long_feature_update_strategy} {config.long_feature_merge_options} {merge_branch}
        '''

        long_feature_commits = f'''
        {self.commit(f'RESUME LONG FEATURE {name}', this_branch)}
        {self.commit('', this_branch)}
        '''

        inner_features = ''.join(
            list(
                itertools.chain(
                    *[
                        (self.feature(feature), merge_inner_feature, long_feature_commits)
                        for feature in short_features
                    ]
                )
            )
        )

        end = f'''        
        git checkout {merge_branch}
        git merge {config.feature_merge_options} {this_branch}
        git branch -d {this_branch}
        # Create a Release
        {self.release(version_type(), name)}
        '''

        return ''.join([start, inner_features, end])

    # def feature_on_feature(self, name: str, merge_branch: str = 'develop') -> str:
    #     name = name.replace(' ', '-')
    #     branch = f'long-feature/{name}'
    #     return textwrap.dedent(
    #         f'''
    #     # Start a long feature
    #     git checkout -b {branch}

    #     {self.commit(f'START LONG FEATURE', branch)}
    #     {self.commit('', branch)}

    #     # Inner Feature
    #     {self.feature(fake.first_name_female())}

    #     # Create Release for Inner Feature
    #     {self.release(version_type(), fake.country())}

    #     # Merge Inner Feature
    #     git checkout {branch}
    #     git {config.long_feature_update_strategy} {config.long_feature_merge_options} {merge_branch}

    #     {self.commit(f'RESUME LONG FEATURE {name}', branch)}
    #     {self.commit('', branch)}

    #     # Inner Feature
    #     {self.feature(fake.first_name_female())}
    #     {self.feature(fake.first_name_female())}

    #     # Create Release for Inner Feature
    #     {self.release(version_type(), fake.country())}

    #     # Merge Inner Feature
    #     git checkout {branch}
    #     git {config.long_feature_update_strategy} {config.long_feature_merge_options} {merge_branch}

    #     {self.commit(f'RESUME LONG FEATURE {name}', branch)}
    #     {self.commit('', branch)}

    #     # ===== FINALLY ===== #
    #     git checkout {merge_branch}
    #     git merge {config.feature_merge_options} {branch}
    #     git branch -d {branch}
    #     '''
    #     )

    def release(self, version_type: str, description: str) -> str:
        """Create a Release

        Start: `develop`
        End: `master`
        1. Create release branch from `develop`
        2. Update the version
        3. Commit
        4. Merge to `master`

        Args:
            version_type (str): 'major', 'minor', 'patch'
            description (str): release description
            base (str, optional): Where to cut release from. Defaults to 'develop'.
            target (str, optional): Where to merge release to. Defaults to 'master'.

        Returns:
            str: git commands
        """
        self.bump_version(version_type)
        description = description.replace(' ', '-')
        release_branch = f'release/{self.version}/{description}'
        return textwrap.dedent(
            f'''
        # Create a release from base to target
        git checkout develop
        git checkout -b {release_branch}
        echo "__version__ = '{self.version}'" > __init__.py
        git add -A
        git commit -m "release: {self.version} - {description}"
        git checkout master
        git merge {config.release_merge_options} {release_branch}
        git tag "{self.version}"
        git checkout develop
        git merge master
        git branch -d {release_branch}
        '''
        )


def version_type():
    return random.choices(population=['major', 'minor', 'patch'], weights=[2, 5, 2], k=1)[0]


def commit_type():
    commit_types_and_weights = {
        'feature': 90,
        'bugfix': 5,
        'refactor': 8,
        'performance': 3,
        'style': 2,
        'test': 30,
        'docs': 20,
        'build': 10,
        'ops': 5,
        'chore': 20,
        'wip': 10,
    }
    return random.choices(
        population=list(commit_types_and_weights.keys()),
        weights=list(commit_types_and_weights.values()),
        k=1,
    )[0]


fake = Faker()

name = fake.file_name().split('.')[0].lower()
repo = GitRepo(name)


if __name__ == '__main__':
    # os.mkdir(name)
    # os.chdir(name)
    new_features = [
        'Create Python Package',
        'Upgrade Testing',
        'Integration Test',
        'Update CSS',
        'NGINX',
        'Continuous Development',
    ]
    commands: list[str] = [
        repo.delete_repo(),
        repo.init_project(),
        repo.feature(new_features[0]),
        repo.long_feature(new_features[1]),
        repo.feature(new_features[2]),
        repo.feature(new_features[3]),
        repo.long_feature(new_features[4]),
        repo.feature(new_features[5]),
    ]
    git_repo = ''.join(commands)
    with open('git-graph.sh', 'w') as f:
        f.writelines(git_repo)
    for line in git_repo.splitlines():
        if not line.startswith('#'):
            commands = []
            commands.append(line)
            subprocess.run(commands, shell=True)
            time.sleep(0.1)
