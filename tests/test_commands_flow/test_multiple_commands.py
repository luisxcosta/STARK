from VICore import Response


def test_multiple_commands(commands_context_flow):
    manager, context, context_delegate = commands_context_flow
    
    @manager.new('foo bar')
    def foobar(): 
        return Response(text = 'foo!')
    
    @manager.new('lorem * dolor')
    def lorem(): 
        return Response(text = 'lorem!')
    
    context.process_string('foo bar lorem ipsum dolor')
    assert len(context_delegate.responses) == 2
    assert context_delegate.responses[0].text == 'foo!'
    assert context_delegate.responses[1].text == 'lorem!'

def test_repeating_command(commands_context_flow):
    manager, context, context_delegate = commands_context_flow
    
    @manager.new('lorem * dolor')
    def lorem(): 
        return Response(text = 'lorem!')
    
    context.process_string('lorem pisum dolor lorem ipsutest_repeating_commanduum dolor sit amet')
    assert len(context_delegate.responses) == 2
    assert context_delegate.responses[0].text == 'lorem!'
    assert context_delegate.responses[1].text == 'lorem!'

def test_overlapping_commands_less_priority_cut(commands_context_flow):
    manager, context, context_delegate = commands_context_flow
    
    @manager.new('foo bar *')
    def foobar(): 
        return Response(text = 'foo!')
    
    @manager.new('* baz')
    def baz(): 
        return Response(text = 'baz!')
    
    result = manager.search('foo bar test baz')
    assert len(result) == 2
    assert result[0].match_result.substring == 'foo bar test'
    assert result[1].match_result.substring == 'baz'

def test_overlapping_commands_priority_cut(commands_context_flow):
    manager, context, context_delegate = commands_context_flow
    
    @manager.new('foo bar *')
    def foobar(): 
        return Response(text = 'foo!')
    
    @manager.new('*t baz')
    def baz(): 
        return Response(text = 'baz!')
    
    result = manager.search('foo bar test baz')
    assert len(result) == 2
    assert result[0].match_result.substring == 'foo bar'
    assert result[1].match_result.substring == 'test baz'

def test_overlapping_commands_remove(commands_context_flow):
    manager, context, context_delegate = commands_context_flow
    
    @manager.new('foo bar')
    def foobar(): 
        return Response(text = 'foo!')
    
    @manager.new('bar baz')
    def barbaz(): 
        return Response(text = 'baz!')
    
    result = manager.search('foo bar baz')
    assert len(result) == 1
    assert result[0].command == foobar
    
def test_overlapping_commands_remove_inverse(commands_context_flow):
    manager, context, context_delegate = commands_context_flow
     
    @manager.new('bar baz')
    def barbaz(): 
        return Response(text = 'baz!')
    
    @manager.new('foo bar')
    def foobar(): 
        return Response(text = 'foo!')
    
    result = manager.search('foo bar baz')
    assert len(result) == 1
    assert result[0].command == barbaz
    
def test_viobjects_parse_caching(commands_context_flow):
    pass