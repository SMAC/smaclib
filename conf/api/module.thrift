#!/usr/bin/thrift --gen py:twisted

# Copyright (C) 2005-2010  MISG/ICTI/EIA-FR
# See LICENSE for details.


include "types.thrift"
include "errors.thrift"


namespace py smaclib.api.module


service Module {
    /** Simple online checking mechanism */
    bool ping()
    
    /** Returns the unique ID of this module on the whole smac network */
    types.ModuleID get_id()
    
    /** Restarts the receiving module */
    oneway void restart()
    
    /** Shuts down the receiving module */
    oneway void shutdown()
    
    list<types.TaskStatus> get_all_tasks()
    
    types.TaskStatus get_task(1: types.TaskID task_id)
                      throws (1: errors.TaskNotFound invalid_task)
    
    void abort_task(1: types.TaskID task_id)
            throws (1: errors.TaskNotFound invalid_task,
                    2: errors.OperationNotSupported invalid_op)
    
    /** Returns true if the task was running */
    bool pause_task(1: types.TaskID task_id)
            throws (1: errors.TaskNotFound invalid_task,
                    2: errors.OperationNotSupported invalid_op)
    
    /** Returns true if the task was paused */
    bool resume_task(1: types.TaskID task_id)
             throws (1: errors.TaskNotFound invalid_task,
                     2: errors.OperationNotSupported invalid_op)
}
