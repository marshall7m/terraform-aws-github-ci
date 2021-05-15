## Process ##
Think about:
- allow for time slot run? (consolidate commits to PR and run tests within x period)
- use terratest instead of pre-commit tf commands given the convenience and integration with multiple tooling (tf, packer, etc.)

- Target repo is loaded to CB
- Buidspec:
    - if event is a push or PR activity (opened or edited):
        - run pre-commit (add flag: --CI-MODE=true for tf running tf apply/destroy)
            - determines what files were changed:
                - if module/foo is changed then run tests/foo and other tests/* that depend on module/foo
            - go into tests/
            - run tf apply
            - if failed then destroy resources and fail build
    - if event is PR merged:
        - create tag/release
        - update chg log for both base and head ref

create mono repo modules with pinned dependencies

repo contains A and B
module A depends on module B

B changes and changes are reflected in version .2

module A still depends on module B but version .1

Module b would be the only module that is tested

only the module within the repo is initialized via `//` backslashes and the module is pinned down

If module B passes tests, repo creates release .2


Scenario 2:

module B and module A change

module B and module A would be tested

module A would change its' dependency pinn to .2

if user looks through .terraform, changes would be in module A and module B, and when module A is init,
it would depend on module B .2

Terrace would have to:
- run tests associated with diff in module
- module A dependency would be relative rather than remote
- if module A passes then module dependency would change to remote new tag

if local relative path depedency, change to remote tag if tests are complete
if module A depends on current B then keep local tag
if module A depends on previous B use remote tag
if module A depends on local B but B changes, 