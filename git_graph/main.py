import enum
import os
import random
import subprocess
import textwrap
import time
from pathlib import Path
from typing import NamedTuple

from colorama import Fore, Style
from faker import Faker


class MergeFlags(enum.Enum):
    no_edit = '--no-edit'  # do not open editor to edit commit message
    no_ff = '--no-ff'  # do not fast-forward merge
    no_commit = '--no-commit'  # perform the merge but do not commit
    squash = '--squash'  # gather changes from all commits and put in staging, requires a subsequent squash commit


class InnerFeature(NamedTuple):
    feature_name: str
    base_branch: str
    merge_branch: str
    merge_flags: set[MergeFlags] | None
    delete_on_merge: bool


class GitHistory:
    """
    Use context manager to automate deleting and creating git repo
    and deleting temp files created during the process.
    """

    SECONDS_DELAY_BETWEEN_COMMANDS = 0.1  # Without delay, sometimes git commands are executed out of order
    TEMP_FILE_PREFIX = 'temp_py_file_'  # Used in commits

    def __init__(
        self,
        interactive: bool = False,
        dry_run: bool = False,
        merge_flags: set[MergeFlags] | None = None,
        target_dir: Path = Path('target/'),
    ):
        self.interactive = interactive
        self.dry_run = dry_run
        self.merge_flags = merge_flags
        self.target_dir = target_dir
        self.fake = Faker(use_weighting=False)
        self.commands: list[str] = []
        if self.interactive and self.dry_run:
            raise ValueError('Cannot be interactive on a dry run')

    def __enter__(self):
        self.change_directory(self.target_dir)
        self.delete_commit_temp_files()
        self.delete_repo()
        self.init_git_repo()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.delete_commit_temp_files(execute=True)
        # Do not delete repo on exit or history is lost and cannot be visualized

    def change_directory(self, directory: Path):
        os.chdir(directory)

    def commit_prefix(self):
        prefixes = ['feat', 'fix', 'docs', 'style', 'refactor', 'perf', 'test', 'chore', 'ops', 'build']
        weights = [20, 6, 3, 1, 3, 1, 6, 4, 2, 1]
        return random.choices(prefixes, weights=weights)[0]

    def command(self, command: str):
        self.commands.append(command)

    def write_commands_to_file(self, filename: str):
        Path(filename).write_text(textwrap.dedent('\n'.join(self.commands)))

    def execute_commands(self):
        # if interactive, print and execute commands only stopping at commits or merges
        #   if user enters 'finish', execute all remaining commands
        # if dry_run, print commands only
        # if not interactive or dry_run, print and execute all commands

        def _execute_and_print_next_command(command: str):
            print(f'{Fore.BLUE}{command}{Style.RESET_ALL}')
            subprocess.run(command, shell=True)
            time.sleep(self.SECONDS_DELAY_BETWEEN_COMMANDS)

        user_prompt = f'{Fore.GREEN}[Enter]{Style.RESET_ALL} for next commit.  {Fore.GREEN}"finish"{Style.RESET_ALL} to run all remaining commands: '
        try:
            if self.interactive:
                user_cmd = None
                for command in self.commands:
                    if not command.startswith(('git commit', 'git merge')):  # only stop and wait on commits or merges
                        _execute_and_print_next_command(command)
                        continue
                    else:
                        while user_cmd != 'finish':
                            _execute_and_print_next_command(command)
                            user_cmd = input(user_prompt)
                            if user_cmd == '':
                                break
                        else:
                            _execute_and_print_next_command(command)
            elif self.dry_run:
                for command in self.commands:
                    print(f'{Fore.BLUE}{command}{Style.RESET_ALL}')
                    print()
            else:
                for command in self.commands:
                    _execute_and_print_next_command(command)
        except KeyboardInterrupt:
            print()
            print(f'{Fore.RED}User CANCELLED{Style.RESET_ALL}')
            print(f'{Fore.YELLOW}Cleaning Temp Files...{Style.RESET_ALL}')
            self.delete_commit_temp_files(execute=True)
            print(f'{Fore.YELLOW}Cleaning Repo...{Style.RESET_ALL}')
            self.delete_repo(execute=True)
            print(f'{Fore.GREEN}Done, Exiting{Style.RESET_ALL}')

    def init_git_repo(self):
        self.command('git init')
        self.command('touch __init__.py')
        self.command("""echo "__version__ = '0.1.0'" > __init__.py""")
        self.command('git add -A')
        self.command('git commit -m "init: Initial Project"')

    def delete_commit_temp_files(self, execute=False):
        command = f'rm {self.TEMP_FILE_PREFIX}*.py > /dev/null 2>&1'
        if execute:  # execute command directly when cleaning up after KeyboardInterrupt
            subprocess.run(command, shell=True)
        else:
            self.command(command)

    def delete_repo(self, execute=False):
        command = 'rm -rf .git'
        if execute:  # execute command directly when cleaning up after KeyboardInterrupt
            subprocess.run(command, shell=True)
        else:
            self.command(command)

    def commit(self, msg: str, branch: str):
        self.command(f'echo "{self.fake.iso8601()}" >> {self.TEMP_FILE_PREFIX}{self.fake.swift11()}.py')
        self.command('git add -A')
        self.command(f'git commit -m "{self.commit_prefix()}: [{branch}] {msg}"')

    def final_commit(self):
        self.delete_commit_temp_files()
        self.command('git add -A')
        self.command('git commit -m "chore: [master] FINAL COMMIT: Deleted all temp files"')

    def feature(
        self,
        feature_name: str,
        base_branch: str = 'master',
        merge_branch: str = 'master',
        merge_flags: set[MergeFlags] | None = None,
        delete_on_merge: bool = True,
        inner_features: list[InnerFeature] = [],
    ):
        merge_flags = merge_flags or self.merge_flags or set()
        merge_flags.add(MergeFlags.no_edit)  # Always no-edit
        parsed_flags = ' '.join([flag.value for flag in merge_flags])
        squash_branch = '--squash' in parsed_flags

        feature_name = feature_name.replace(' ', '-')
        this_branch = f'{"long-feature" if inner_features else "feature"}/{feature_name}'

        create_feature_branch = f'git checkout -b {this_branch} {base_branch}'
        checkout_this_branch = f'git checkout {this_branch}'
        checkout_target_branch = f'git checkout {merge_branch}'
        merge_this_branch = f'git merge {parsed_flags} {this_branch}'

        # Create feature branch
        self.command(create_feature_branch)

        # Add Commits that show commands to visualize in graph
        self.commit(msg=create_feature_branch, branch=this_branch)
        self.commit(msg='regular commit', branch=this_branch)

        if inner_features:
            for inf in inner_features:
                self.feature(
                    feature_name=inf.feature_name,
                    base_branch=this_branch if inf.base_branch == 'feature' else inf.base_branch,
                    merge_branch=this_branch if inf.merge_branch == 'feature' else inf.merge_branch,
                    merge_flags=inf.merge_flags,
                    delete_on_merge=inf.delete_on_merge,
                )
                # Add commits to long feature branch between features for testing variance
                self.command(checkout_this_branch)
                self.commit(msg=checkout_this_branch, branch=this_branch)
                self.commit(msg='regular commit', branch=this_branch)

            # Final long feature commit if inner features
            self.commit(msg=f'FINISH LONG FEATURE: {feature_name}', branch=this_branch)

        # Add Commits that show commands to visualize in graph
        self.commit(msg=checkout_target_branch, branch=this_branch)
        self.commit(msg=merge_this_branch, branch=this_branch)

        # Merge feature branch into target branch
        self.command(checkout_target_branch)
        self.command(merge_this_branch)

        if squash_branch:  # Squash commit required if branch is squashed
            self.command(f'git commit -m "feat: {feature_name} SQUASHED"')

        if delete_on_merge:  # must -D force delete if squashed
            self.command(f'git branch {"-D" if squash_branch else "-d"} {this_branch}')


if __name__ == '__main__':
    DRY_RUN = False
    with GitHistory(dry_run=DRY_RUN, merge_flags={MergeFlags.no_ff}) as gh:
        merge_flags = {MergeFlags.no_ff}
        delete_on_merge = True

        inner_features = [
            InnerFeature(
                feature_name='base=feature target=master',
                base_branch='feature',
                merge_branch='master',
                merge_flags=merge_flags,
                delete_on_merge=delete_on_merge,
            ),
            InnerFeature(
                feature_name='base=feature target=feature',
                base_branch='feature',
                merge_branch='feature',
                merge_flags=merge_flags,
                delete_on_merge=delete_on_merge,
            ),
            InnerFeature(
                feature_name='base=master target=master',
                base_branch='master',
                merge_branch='master',
                merge_flags=merge_flags,
                delete_on_merge=delete_on_merge,
            ),
            InnerFeature(
                feature_name='base=master target=feature',
                base_branch='master',
                merge_branch='feature',
                merge_flags=merge_flags,
                delete_on_merge=delete_on_merge,
            ),
        ]

        gh.commit(msg='FIRST COMMIT', branch='master')
        gh.feature('experiment 01')
        # gh.feature('MVP 02')
        # gh.feature('refactor 01', inner_features=inner_features)
        # gh.commit(msg='commit after refactor 01', branch='master')
        # gh.feature('new feature 03')
        # gh.feature('refactor shit code 02', inner_features=inner_features)
        # gh.feature('shiny feature 04')
        # gh.feature('dumb dashboards 05', inner_features=[inner_features[0], inner_features[2]])
        gh.commit(msg='commit before bugfix', branch='master')
        # gh.feature('bugfix cicd 06')
        # gh.feature('huge feature 03', inner_features=[inner_features[1], inner_features[3]])
        # gh.feature('little refactor 07')
        gh.final_commit()

        gh.write_commands_to_file('git-commands.sh')

        gh.execute_commands()
