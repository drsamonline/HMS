# IPD Management

An admission is an episode: a patient, a bed, a start and an end.

A bed is occupied from admission until discharge. The bed census is the count of beds
that are occupied right now, which is why discharging a patient frees the bed in the
same action.

A discharge records **how the episode ended** - routine, expired, against advice or
transferred. That is not the same as whether the record is valid, and the difference
is what makes mortality measurable.
