# vim:ts=4 sw=4 et:

import os
import sys
import time

from mcp.server.fastmcp import FastMCP

ue5_root= os.environ.get('UE5_ENGINE_ROOT', 'C:/Program Files/Epic Games/UE_5.8')
sys.path.append( os.path.join( ue5_root, 'Engine/Plugins/Experimental/PythonScriptPlugin/Content/Python' ) )
from remote_execution import RemoteExecution

mcp= FastMCP('ue5-python', json_response=True)

#------------------------------------------------------------------------------

logger= None
def print_err( *msg ):
    if True:
        print( *msg, file=sys.stderr )
    else:
        global logger
        if not logger:
            logger= open( 'log.txt', 'w' )
        logger.write( ' '.join([ str(m) for m in msg]) + '\n' )
        logger.flush()


class UEInterface:
    def __init__( self ):
        self.remote_exec= None

    def find_node( self, nodes, machine ):
        for node in nodes:
            if machine == '*':
                return  node.get('node_id')
            pc= node.get('machine')
            if pc == machine:
                return  node.get('node_id')
        print_err( 'Error: UE5 node %s not found' % machine )
        return  None

    def connect( self ):
        if not self.remote_exec:
            self.remote_exec= RemoteExecution()
            self.remote_exec.start()
            time.sleep( 1 )
            hostname= os.environ.get('COMPUTERNAME',os.environ.get('HOST',os.environ.get('HOSTNAME','*')))
            node_id= self.find_node( self.remote_exec.remote_nodes, hostname )
            if node_id:
                self.remote_exec.open_command_connection( node_id )

    def disconnect( self ):
        if self.remote_exec:
            self.remote_exec.stop()
            self.remote_exec= None

    def script_wrapper( self, script ):
        out_str= 'try:\n'
        for line in script.split('\n'):
            out_str+= ' ' + line + '\n'
        out_str+= '\nexcept Exception as e:\n print("Error:",str(e))\n'
        return  out_str

    def exec( self, script ):
        wrapped= self.script_wrapper( script )
        result= self.remote_exec.run_command( wrapped )
        return  result

    def is_valid( self ):
        return  self.remote_exec

ueinterface= None

def get_api():
    global ueinterface
    if not ueinterface:
        ueinterface= UEInterface()
        ueinterface.connect()
    return  ueinterface

#------------------------------------------------------------------------------


@mcp.tool()
def run_ue5python( script:str ) -> str:
    """
    UE5 の remote_execution 機能を使って python script を実行します。
    UE5 の python api を呼び出すことが出来ます。

    Args:
        script     実行するpythonスクリプト
    """
    api= get_api()
    if not api.is_valid():
        return  'Error: Unable to connect to UE5'
    result= api.exec( script )
    success= result.get('success',False)
    output= result.get('output')
    return  str( { 'success': success, 'output': str(output) } )


#------------------------------------------------------------------------------


if __name__=='__main__':
    mcp.run(transport='stdio')

