// General literature questions offered next to a structure the reviewer is looking at.
// They are deliberately about published evidence, never about this scan: the literature
// assistant has no access to the image and must not diagnose, stage or certify (RF1–RF9).
// Selecting one only fills the Ask box; the reviewer still decides whether to send it.
const QUESTIONS = {
  pancreas: [
    'Why can pancreas boundaries be hard to outline on CT?',
    'How does normal pancreas size and shape vary between people?',
  ],
  lesion: [
    'Why can pancreatic lesion boundaries be hard to see on CT?',
    'How does measuring pancreatic tumor diameter differ from measuring its volume on CT?',
  ],
  referenceLesion: [
    'How do expert annotators define pancreatic lesion boundaries in reference datasets?',
    'Why can pancreatic lesion boundaries be hard to see on CT?',
  ],
  difference: [
    'How much do readers disagree when outlining the pancreas or pancreatic lesions?',
    'What errors do automated pancreas segmentation models commonly make?',
  ],
}

export function structureQuestions(object) {
  if (!object) return []
  if (object.source === 'difference') return QUESTIONS.difference
  if (object.anatomy === 'lesion') return object.source === 'gt' ? QUESTIONS.referenceLesion : QUESTIONS.lesion
  return QUESTIONS.pancreas
}
