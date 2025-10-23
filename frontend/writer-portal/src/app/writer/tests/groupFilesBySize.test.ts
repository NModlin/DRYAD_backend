import { groupFilesBySize } from '@/lib/api';

function makeFile(name: string, sizeMB: number) {
  const size = Math.max(1, Math.floor(sizeMB * 1024 * 1024));
  return new File([new Uint8Array(size)], name);
}

test('groups files into ~50MB batches', () => {
  const files = [
    makeFile('a', 10),
    makeFile('b', 25),
    makeFile('c', 20),
    makeFile('d', 5),
  ];
  const batches = groupFilesBySize(files, 50);
  expect(batches.length).toBe(2);
  expect(batches[0].map(f => f.name)).toEqual(['a','b']);
  expect(batches[1].map(f => f.name)).toEqual(['c','d']);
});

test('large single file becomes its own batch', () => {
  const files = [makeFile('huge', 120), makeFile('small', 5)];
  const batches = groupFilesBySize(files, 50);
  expect(batches.length).toBe(2);
  expect(batches[0][0].name).toBe('huge');
});

