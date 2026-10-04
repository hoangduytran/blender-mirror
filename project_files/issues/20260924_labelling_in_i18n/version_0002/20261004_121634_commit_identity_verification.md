# Commit identity verification

The feature commits in both checkouts use Hoang Duy Tran <hoangduytran1960@gmail.com> as author and committer. The account name is hoanguk. Repository-local configuration is set; global configuration is unchanged.

All 37 earlier original feature commits and all 40 earlier destination feature commits were checked. Their earlier email was googlemail.com. The correction changes only author and committer identity and the resulting parent references. Every old and new commit has the same file tree, message, and dates. No prohibited credit or co-author trailer was found. Upstream commits were excluded. Both remotes returned no published feature branch before the correction.

The old-to-new maps are in [original map](review/evidence/20261004-authorship/original-commit-map.json) and [destination map](review/evidence/20261004-authorship/destination-commit-map.json). Historical test logs keep the hashes recorded when the tests ran. These results remain valid because the code did not change. Recovery bundles are retained locally outside the repositories.

The independent attribution check also covers source comments and submission documents. Technical uses of “generated” describe Blender behavior, not authorship. Historical chat quotes remain faithful to what was said.

The single document difference was a historical-record notice in the implementation progress report. Both checkouts now contain that notice. The unrelated Console edit remains outside this feature.

To list every feature commit, including later documentation commits, run in either checkout:

```sh
git log --reverse main..HEAD --format='Commit: %H%nAuthor: %an%nAuthor email: %ae%nSubject: %s%n'
git log --reverse main..HEAD --format='%H %an <%ae> | %cn <%ce>'
git config user.name
git config user.email
git show -s --format=fuller HEAD
```

All implementation and verification results remain unchanged: 77 focused C++ tests, nine reviewer checks, six runner self-checks, 40 broader/search tests, seven existing Python suites, 14 typing variants, three undo checks, and 15-file/353-ID preservation pass. Required visible checks were confirmed by the user. No implementation blocker remains.
