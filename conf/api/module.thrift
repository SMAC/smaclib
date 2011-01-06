#!/usr/bin/thrift --gen py:twisted

# Copyright (C) 2005-2010  MISG/ICTI/EIA-FR
# See LICENSE for details.


namespace py smaclib.api.module


service Module {
    /** Simple online checking mechanism */
    void ping(),
    
    /** Restarts the receiving module */
    oneway void restart(),
    
    /** Shuts down the receiving module */
    oneway void shutdown(),
}
