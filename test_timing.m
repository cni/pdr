%#!/usr/bin/env octave

WaitSecs(0.5);
unix('startScan');
startSecs = GetSecs();
secs = [];
running = 1;
while(running)
    secs(end+1) = KbWait() - startSecs;
    WaitSecs(0.1);
    printf('   %0.4f\n', secs(end));
    fflush(stdout);
end


