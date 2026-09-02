# Reference images

Drop the design references here, named for the view they were shot from:

| file | view |
|---|---|
| `side.png` | side elevation |
| `front.png` | head-on |
| `rear.png` | from behind |

`car_blockout.build(references=True)` creates a viewport image empty for each.
They never appear in a render — they are modelling reference only — and each is
set to show only when the view is aligned with it, so the side image does not
clutter the front view.

Alignment needs two numbers per image that cannot be read off the model: how
much of the frame the car fills (`span`) and where its centre sits (`centre`).
The defaults assume the car is centred and fills most of the frame. If a
reference sits off, adjust its `span` rather than dragging the empty, so the
scale stays honest.
