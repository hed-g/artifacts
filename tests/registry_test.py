# -*- coding: utf-8 -*-
"""Tests for the artifact definitions registry."""

import io
import unittest

from artifacts import errors
from artifacts import reader
from artifacts import registry
from artifacts import source_type

from tests import test_lib


class TestSourceType(source_type.SourceType):
  """Class that implements a test source type."""

  TYPE_INDICATOR = 'test'

  def __init__(self, test=None):
    """Initializes the source type object.

    Args:
      test (Optional[str]): test string.

    Raises:
      FormatError: when test is not set.
    """
    if not test:
      raise errors.FormatError('Missing test value.')

    super(TestSourceType, self).__init__()
    self.test = test

  def AsDict(self):
    """Represents a source type as a dictionary.

    Returns:
      dict[str, str]: source type attributes.
    """
    return {'test': self.test}


class ArtifactDefinitionsRegistryTest(test_lib.BaseTestCase):
  """Tests for the artifact definitions registry."""

  # pylint: disable=protected-access

  def testArtifactDefinitionsRegistry(self):
    """Tests the ArtifactDefinitionsRegistry functions."""
    test_file = self._GetTestFilePath(['definitions.yaml'])
    self._SkipIfPathNotExists(test_file)

    artifact_registry = registry.ArtifactDefinitionsRegistry()

    artifact_reader = reader.YamlArtifactsReader()

    for artifact_definition in artifact_reader.ReadFile(test_file):
      artifact_registry.RegisterDefinition(artifact_definition)

    # Make sure the test file got turned into artifacts.
    self.assertEqual(len(artifact_registry.GetDefinitions()), 7)

    artifact_definition = artifact_registry.GetDefinitionByName('EventLogs')
    self.assertIsNotNone(artifact_definition)

    # Try to register something already registered
    with self.assertRaises(KeyError):
      artifact_registry.RegisterDefinition(artifact_definition)

    # Deregister
    artifact_registry.DeregisterDefinition(artifact_definition)

    # Check it is gone
    with self.assertRaises(KeyError):
      artifact_registry.DeregisterDefinition(artifact_definition)

    self.assertEqual(len(artifact_registry.GetDefinitions()), 6)

    test_artifact_definition = artifact_registry.GetDefinitionByName(
        'SecurityEventLogEvtxFile')
    self.assertIsNotNone(test_artifact_definition)

    self.assertEqual(test_artifact_definition.name, 'SecurityEventLogEvtxFile')
    self.assertEqual(test_artifact_definition.aliases, ['SecurityEventLogEvtx'])

    expected_description = (
        'Windows Security Event log for Vista or later systems.')
    self.assertEqual(test_artifact_definition.description, expected_description)

    bad_args = io.BytesIO(
        b'name: SecurityEventLogEvtx\n'
        b'doc: Windows Security Event log for Vista or later systems.\n'
        b'sources:\n'
        b'- type: FILE\n'
        b'  attributes: {broken: [\'%%environ_systemroot%%\\System32\\'
        b'winevt\\Logs\\Security.evtx\']}\n'
        b'supported_os: [Windows]\n'
        b'urls: [\'http://www.forensicswiki.org/wiki/\n'
        b'Windows_XML_Event_Log_(EVTX)\']\n')

    generator = artifact_reader.ReadFileObject(bad_args)
    with self.assertRaises(errors.FormatError):
      next(generator)

  def testSourceTypeFunctions(self):
    """Tests the source type functions."""
    number_of_source_types = len(
        registry.ArtifactDefinitionsRegistry._source_type_classes)

    registry.ArtifactDefinitionsRegistry.RegisterSourceType(TestSourceType)

    self.assertEqual(
        len(registry.ArtifactDefinitionsRegistry._source_type_classes),
        number_of_source_types + 1)

    with self.assertRaises(KeyError):
      registry.ArtifactDefinitionsRegistry.RegisterSourceType(TestSourceType)

    registry.ArtifactDefinitionsRegistry.DeregisterSourceType(TestSourceType)

    self.assertEqual(
        len(registry.ArtifactDefinitionsRegistry._source_type_classes),
        number_of_source_types)

    registry.ArtifactDefinitionsRegistry.RegisterSourceTypes([TestSourceType])

    self.assertEqual(
        len(registry.ArtifactDefinitionsRegistry._source_type_classes),
        number_of_source_types + 1)

    with self.assertRaises(KeyError):
      registry.ArtifactDefinitionsRegistry.RegisterSourceTypes([TestSourceType])

    source_object = registry.ArtifactDefinitionsRegistry.CreateSourceType(
        'test', {'test': 'test123'})

    self.assertIsNotNone(source_object)
    self.assertEqual(source_object.test, 'test123')

    with self.assertRaises(errors.FormatError):
      source_object = registry.ArtifactDefinitionsRegistry.CreateSourceType(
          'test', {})

    with self.assertRaises(errors.FormatError):
      source_object = registry.ArtifactDefinitionsRegistry.CreateSourceType(
          'bogus', {})

    registry.ArtifactDefinitionsRegistry.DeregisterSourceType(TestSourceType)


if __name__ == '__main__':
  unittest.main()
