# Delayed Result Challenges for CTFd

The submission is always correct?

Once a user is marked as solved, the item goes green
The site won't allow resubmission if solved

But we do want to accept any input without it erroring?

So we need override attempt(), solve() and fail()

attempt() -> always return True
solve() -> don't actually add to solve unless time ready
fail() -> set schedule to test and change to solve?