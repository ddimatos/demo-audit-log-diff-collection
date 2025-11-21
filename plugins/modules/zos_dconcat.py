#!/usr/bin/python

DOCUMENTATION = r'''
---
module: zos_dconcat

short_description: Concatenate dataset differences.
version_added: "1.0.0"

description: This module diffs two datasets and will concatenate the result. 

options:
    src:
        description: Source dataset
        required: true
        type: str
    change:
        description: Dataset with the changes.
        required: true
        type: str
    merge:
        description: Dataset to merge results into.
        required: false
        type: str
    state:
        description:
            - Control to demo if the result of this module is changed or not.
            - Parameter description can be a list as well.
        required: false
        type: str
        choices:
            - default
            - reverse
            - audit
author:
    - Demetrios Dimatos (@ddimatos)
'''

EXAMPLES = r'''
- name: "Diff {{ src }} with {{ change }} and append differences to {{ change }}"
    zos_dconcat:
        src: "{{ src }}"
        change: "{{ change }}"
        merge: "{{ merge }}"

    - name: "Diff {{ src }} with {{ change }} and append differences to {{ change }}"
      zos_dconcat:
        src: "{{ src }}"
        change: "{{ change }}"
        state: "reverse"
      register: result

    - name: "Diff {{ src }} with {{ change }} and append differences to {{ src }}"
      zos_dconcat:
        src: "{{ src }}"
        change: "{{ change }}"
      register: result
'''

RETURN = r'''
src:
    description: The source dataset
    type: str
    returned: always
    sample: 'some.data.set'
change:
    description: The dataset with changes.
    type: str
    returned: always
    sample: 'some.data.set'
merge:
    description: The merge dataset.
    type: str
    returned: always
    sample: 'some.data.set'
state:
    description: State, can be either 'default' or 'reverse'
    type: str
    returned: always
    sample: 'reverse'
stdout:
    description: The dataset diff merge result as a string.
    type: str
    returned: success
    sample: "WILLIAM            BENSON              HR124     HUMAN RESOURCES                \nWILLIAM"
stdout_lines:
    description: The dataset diff merge result as a list.
    type: str
    returned: on-success
    sample: [
        "WILLIAM            BENSON              HR124     HUMAN RESOURCES                ",
        "WILLIAM            BALES               MG882     MANAGEMENT                     ",
        "TINA               STATES              AP592     ACCOUNTS PAYABLE               ",
        "CAROL              SCHNEIDER           IT457     IT                             "
    ]
'''

from ansible.module_utils.basic import AnsibleModule

# This import relies on the wheel being present and in PYTHONNPATH, see following comment about module_utils                                                                                                                                                                                                     # type: ignore
from module.dconcat_module import dconcat, ddiff_source, ddiff_change, data_set_print, ddiff_source_write

# If you want to use the module utils that is included in the collection instead of the wheel, uncomment this import.
# from ansible_collections.ddimatos.zos_modules.plugins.module_utils.dconcat_module import dconcat, ddiff_source, ddiff_change, data_set_print

def run_module():
    output = None
    reverse = None
    audit = None
    # Define available arguments/parameters a user can pass to the module
    module_args = dict(
        src = dict(required=True, type='str'),
        change = dict(required=True, type='str'),
        merge = dict(required=False, type='str', default=None),
        state = dict(required=False, choices=['default', 'reverse', 'audit'], default='default')
    )

    module = AnsibleModule(
        argument_spec=module_args,
        supports_check_mode=False
    )

    src = module.params['src']
    change = module.params['change']
    merge = module.params['merge']
    state = module.params['state']

    result = dict(
        changed = False,
        stdout ='',
        stdout_lines = [],
        src = src,
        change = change,
        merge = merge,
        state = state,
        rc='',
        failed = False
    )

    # Merge overrides reverse
    if state == 'audit':
        audit = True
    elif merge is not None:
        reverse = False
    elif state == 'reverse':
        reverse = True

    # Perform the diff and concat via previously created Python module code
    output = None

    if audit:
        rc = ddiff_source_write(source=src, change=change, merge=merge)

        if rc == 0:
            output = data_set_print(source=merge)
            result['stdout'] = output
            result['stdout_lines'] = output.splitlines()
            result['rc'] = 6
            module.exit_json(**result)
    else:
        rc = dconcat( source=src, change=change, merge=merge, reverse=state)
        if rc == 0:
            if reverse:
                output = data_set_print(source=change)
            elif merge is not None:
                output = data_set_print(source=merge)
            else:
                output = data_set_print(source=src)

            result['stdout'] = output
            result['stdout_lines'] = output.splitlines()
            result['rc'] = rc
            module.exit_json(**result)

    result["changed"] = False
    result["failed"] = True
    result['stdout'] = output
    result['rc'] = rc
    result["msg"] = ("Unable to diff and concat src dataset {0} to change"
                    " dataset {1}.".format(src,change))
    module.fail_json(**result)

def main():
    run_module()


if __name__ == '__main__':
    main()